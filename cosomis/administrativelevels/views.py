import os
import re
import json
import zipfile
import requests
from io import BytesIO
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.views.generic import DetailView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from usermanager.permissions import AdminPermissionRequiredMixin
from .forms import AdministrativeLevelForm
from cosomis.mixins import PageMixin
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import QuerySet, Subquery, OuterRef, Value
from django.db.models.functions import Coalesce

from administrativelevels.models import AdministrativeLevel, Phase, Activity, Task
from investments.models import Attachment, Investment

from .forms import AttachmentFilterForm, VillageSearchForm


class AdministrativeLevelsListView(PageMixin, LoginRequiredMixin, ListView):
    """Display administrative level list"""

    model = AdministrativeLevel
    queryset = []  # AdministrativeLevel.objects.filter(type="Village")
    template_name = "administrative_level/list.html"
    context_object_name = "administrativelevels"
    title = _("Administrative levels")
    active_level1 = "administrative_levels"
    breadcrumb = [
        {"url": "", "title": title},
    ]

    def get_queryset(self):
        search = self.request.GET.get("search", None)
        page_number = self.request.GET.get("page", None)
        _type = self.request.GET.get("type", "Village")
        if search:
            if search == "All":
                ads = AdministrativeLevel.objects.filter(type=_type)
                return Paginator(ads, ads.count()).get_page(page_number)
            search = search.upper()
            return Paginator(
                AdministrativeLevel.objects.filter(type=_type, name__icontains=search),
                100,
            ).get_page(page_number)
        else:
            return Paginator(
                AdministrativeLevel.objects.filter(type=_type), 100
            ).get_page(page_number)

        # return super().get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super(AdministrativeLevelsListView, self).get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("search", None)
        ctx["type"] = self.request.GET.get("type", "Village")
        return ctx


class AdministrativeLevelCreateView(
    PageMixin, LoginRequiredMixin, AdminPermissionRequiredMixin, CreateView
):
    model = AdministrativeLevel
    template_name = "administrative_level/create.html"
    context_object_name = "administrativelevel"
    title = _("Create Administrative level")
    active_level1 = "administrative_levels"
    breadcrumb = [
        {"url": "", "title": title},
    ]

    def get_parent(self, type: str):
        parent = None
        if type == "Prefecture":
            parent = "Region"
        elif type == "Commune":
            parent = "Prefecture"
        elif type == "Canton":
            parent = "Commune"
        elif type == "Village":
            parent = "Canton"
        return parent

    form_class = AdministrativeLevelForm  # specify the class form to be displayed

    def get_context_data(self, **kwargs):
        type = self.request.GET.get("type")
        context = super().get_context_data(**kwargs)
        context["form"] = AdministrativeLevelForm(self.get_parent(type), type)
        return context

    def post(self, request, *args, **kwargs):
        form = AdministrativeLevelForm(
            self.get_parent(self.request.GET.get("type")), request.POST
        )
        if form.is_valid():
            form.save()
            return redirect("administrativelevels:list")
        return super(AdministrativeLevelCreateView, self).get(request, *args, **kwargs)


class AdministrativeLevelDetailView(
    PageMixin, LoginRequiredMixin, DetailView
):
    """Class to present the detail page of one village"""

    model = AdministrativeLevel
    template_name = "administrative_level/detail/index.html"
    active_level1 = "administrative_levels"

    def get_context_data(self, **kwargs):
        context = super(AdministrativeLevelDetailView, self).get_context_data(**kwargs)

        if "object" in context:
            context["title"] = "%s %s" % (_(context['object'].type), context['object'].name)
            if context["object"].is_village():
                context["investments"] = Investment.objects.filter(
                    administrative_level=self.object
                )
        admin_level = context.get("object")

        context["context_object_name"] = admin_level.type.lower()

        context['phases'] = self._get_planning_cycle()

        tasks_qs = Task.objects.filter(activity__phase__village=admin_level)
        current_task = tasks_qs.filter(status=Task.IN_PROGRESS).first()
        current_activity = current_task.activity if current_task else None
        current_phase = current_activity.phase if current_activity else None

        task_number = tasks_qs.count()
        tasks_done = tasks_qs.filter(status=Task.COMPLETED).count()
        context["planning_status"] = {
            "current_phase": current_phase,
            "current_activity": current_activity,
            "current_task": current_task,
            "completed": round(float(tasks_done) * 100 / float(task_number), 2) if task_number != 0 else '-',
            "priorities_identified": context["object"].identified_priority,
            "village_development_plan_date": "",
            "facilitator": "",
        }

        images = Attachment.objects.filter(
            adm=admin_level, type=Attachment.PHOTO
        ).all()[:5]
        context["images_data"] = {
            "images": images,
            "exists_at_least_image": len(images) != 0,
            "first_image": images[0] if len(images) > 0 else None,
        }

        context["investments"] = Investment.objects.filter(
            administrative_level=admin_level.id
        )
        context["mapbox_access_token"] = os.environ.get("MAPBOX_ACCESS_TOKEN")
        self.object.latitude = 10.693749945416448
        self.object.longitude = 0.330183201548857
        return context

    def _get_planning_cycle(self):
        phases = list()
        admin_level = self.object
        for phase in admin_level.phases.all():
            phase_node = {
                "id": phase.id,
                "name": phase.name,
                "order": phase.order,
                "activities": list(),
            }
            activities_status = None
            for activity in phase.activities.all():
                activity_node = {
                    "id": activity.id,
                    "name": activity.name,
                    "order": activity.order,
                    "tasks": list(),
                }
                tasks_status = None
                for task in activity.tasks.all():
                    task_node = {
                        "id": task.id,
                        "name": task.name,
                        "order": task.order,
                        "status": task.status,
                    }
                    activity_node["tasks"].append(task_node)
                    if tasks_status is None:
                        tasks_status = task.status
                    if task.status != Task.ERROR:
                        if tasks_status == Task.COMPLETED and task.status == Task.IN_PROGRESS:
                            tasks_status = Task.IN_PROGRESS
                    else:
                        tasks_status = Task.ERROR
                activity_node["status"] = tasks_status
                phase_node["activities"].append(activity_node)
                if activities_status is None:
                    activities_status = tasks_status
                if activity_node["status"] != Task.ERROR:
                    if activities_status == Task.COMPLETED and activity_node["status"] == Task.IN_PROGRESS:
                        activities_status = Task.IN_PROGRESS
                else:
                    activities_status = Task.ERROR
            phase_node["status"] = activities_status
            phases.append(phase_node)
        return phases


class AdministrativeLevelSearchListView(PageMixin, LoginRequiredMixin, ListView):
    """Display administrative level list by parent choice"""

    model = AdministrativeLevel
    queryset = []
    template_name = "administrative_level/list.html"
    context_object_name = "administrativelevels"
    title = _("Administrative levels")
    active_level1 = "administrative_levels"
    breadcrumb = [
        {"url": "", "title": title},
    ]

    def get_queryset(self):
        search = self.request.GET.get("search", None)
        page_number = self.request.GET.get("page", None)
        _type = self.request.GET.get("type", "Village")
        if search:
            if search == "All":
                ads = AdministrativeLevel.objects.filter(type=_type)
                return Paginator(ads, ads.count()).get_page(page_number)
            search = search.upper()
            return Paginator(
                AdministrativeLevel.objects.filter(type=_type, name__icontains=search),
                100,
            ).get_page(page_number)
        else:
            return Paginator(
                AdministrativeLevel.objects.filter(type=_type), 100
            ).get_page(page_number)

    def get_context_data(self, **kwargs):
        ctx = super(AdministrativeLevelSearchListView, self).get_context_data(**kwargs)
        ctx["form"] = VillageSearchForm()
        ctx["search"] = self.request.GET.get("search", None)
        ctx["type"] = self.request.GET.get("type", "Village")
        ctx["current_language"] = translation.get_language()
        return ctx


# Attachments
class AttachmentListView(PageMixin, LoginRequiredMixin, ListView):
    template_name = "attachments/attachments.html"
    context_object_name = "attachments"
    title = _("Gallery")
    paginate_by = 10
    model = Attachment

    filter_hierarchy = [
        'task',
        'activity',
        'phase'
    ] + [adm_type[0].lower() for adm_type in AdministrativeLevel.TYPE]

    def post(self, request, *args, **kwargs):
        url = reverse("administrativelevels:attachments")
        final_querystring = request.GET.copy()

        for key, value in request.GET.items():
            if (
                key in request.POST
                and value != request.POST[key]
                and request.POST[key] != ""
            ):
                final_querystring.pop(key)

        post_dict = request.POST.copy()
        post_dict.update(final_querystring)
        post_dict.pop("csrfmiddlewaretoken")
        if "reset-hidden" in post_dict and post_dict["reset-hidden"] == "true":
            return redirect(url)

        for key, value in request.POST.items():
            if value == "":
                post_dict.pop(key)
        final_querystring.update(post_dict)
        if final_querystring:
            url = "{}?{}".format(url, urlencode(final_querystring))
        return redirect(url)

    def get_context_data(self, **kwargs):
        context = super(AttachmentListView, self).get_context_data(**kwargs)

        context["regions"] = AdministrativeLevel.objects.filter(
            type=AdministrativeLevel.REGION
        )

        query_params: dict = self.request.GET

        context["filter_hierarchy_query_strings"] = self.build_filter_hierarchy()
        context["query_strings_raw"] = query_params.copy()
        context["query_strings_raw"].pop("page", None)
        babylong_query_params_list = [key + '=' + value for key, value in context["query_strings_raw"].items()]
        if babylong_query_params_list:
            context["babylong_query_params"] = '&' + '&'.join(babylong_query_params_list)

        form = AttachmentFilterForm()

        paginator= self.__build_db_filter()

        context["no_results"] = paginator.count == 0
        context["current_language"] = translation.get_language()
        page_number = int(query_params.get("page", 1))
        context["attachments"] = paginator.get_page(page_number) if page_number <= paginator.num_pages else []
        context["form"] = form
        return context

    def get_template_names(self, *args, **kwargs):
        if self.request.htmx:
            return "attachments/_grid.html"
        else:
            return self.template_name

    def __build_db_filter(self) -> Paginator:
        query: QuerySet = self.get_queryset()

        query = query.order_by("created_date")
        paginator = Paginator(query, 36)

        return paginator

    def build_filter_hierarchy(self):
        resp = {}

        def _build_filter_hierarchy(index, get_value):
            current_filter_level = self.filter_hierarchy[index]
            next_filter_level = self.filter_hierarchy[index + 1] if index + 1 < len(self.filter_hierarchy) else None
            if current_filter_level == "task":
                task = Task.objects.get(id=int(get_value))
                resp[current_filter_level] = task.id
                resp[next_filter_level] = task.activity.id
            if current_filter_level == "activity":
                activity = Activity.objects.get(id=int(get_value))
                resp[current_filter_level] = activity.id
                resp[next_filter_level] = activity.phase.id
            if current_filter_level == "phase":
                phase = Phase.objects.get(id=int(get_value))
                resp[current_filter_level] = phase.id
                resp[next_filter_level] = phase.village.id
            if current_filter_level in [adm_type[0].lower() for adm_type in AdministrativeLevel.TYPE]:
                adm_lvl = AdministrativeLevel.objects.get(id=int(get_value))
                resp[current_filter_level] = adm_lvl.id
                if hasattr(adm_lvl, "parent") and adm_lvl.parent is not None and len(self.filter_hierarchy) > index + 1:
                    resp[next_filter_level] = adm_lvl.parent.id

            if len(self.filter_hierarchy) > index + 1:
                return _build_filter_hierarchy(index + 1, resp[next_filter_level])
            return resp

        for idx, key_filter in enumerate(self.filter_hierarchy):
            if key_filter in self.request.GET and self.request.GET[key_filter] not in ['', None]:
                resp = _build_filter_hierarchy(idx, self.request.GET[key_filter])
                return json.dumps(resp)

    def get_queryset(self):
        queryset = super().get_queryset()
        empty_list = ["", None]

        if "tasks" in self.request.GET and self.request.GET["tasks"] not in empty_list:
            queryset = queryset.filter(
                task__id=self.request.GET["tasks"]
            )
        elif "activities" in self.request.GET and self.request.GET["activities"] not in empty_list:
            queryset = queryset.filter(
                task__activity__id=self.request.GET["activities"]
            )
        elif "phase" in self.request.GET and self.request.GET["phase"] not in empty_list:
            queryset = queryset.filter(
                task__activity__phase__id=self.request.GET["phase"]
            )
        else:
            adm_lvls = [adm_name[0].lower() for adm_name in AdministrativeLevel.TYPE]
            adm_list = [adm_type for adm_type in adm_lvls if adm_type in self.request.GET]
            adm_type = adm_list[0] if adm_list else None

            if adm_type and self.request.GET[adm_type] not in empty_list:
                queryset = queryset.filter(adm__id=self.request.GET[adm_type])

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset


@login_required
def attachment_download(self, adm_id: int, url: str):
    response = requests.get(url)
    if response.status_code == 200:
        content_disposition = response.headers.get("content-disposition")
        filename = url.split("/")[-1]
        if content_disposition is not None:
            try:
                fname = re.findall('filename="(.+)"', content_disposition)

                if len(fname) != 0:
                    filename = fname[0]
            except:
                pass

        response = HttpResponse(
            response.content, content_type=response.headers.get("content-type")
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    else:
        return HttpResponse("Failed to download the file.")


@login_required
def attachment_download_zip(self, adm_id: int):
    ids = self.GET.get("ids").split(",")

    buffer = BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w")
    for id in ids:
        url = Attachment.objects.get(id=int(id)).url
        response = requests.get(url)
        if response.status_code == 200:
            content_disposition = response.headers.get("content-disposition")
            filename = url.split("/")[-1]
            if content_disposition is not None:
                try:
                    fname = re.findall('filename="(.+)"', content_disposition)

                    if len(fname) != 0:
                        filename = fname[0]
                except:
                    pass
        zip_file.writestr(filename, response.content)

    zip_file.close()

    response = HttpResponse(buffer.getvalue())
    response["Content-Type"] = "application/x-zip-compressed"
    response["Content-Disposition"] = "attachment; filename=attachments.zip"

    return response
