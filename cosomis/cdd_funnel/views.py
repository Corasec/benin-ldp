import csv

from django.http import HttpResponse
from django.views import generic

from administrativelevels.models import Task, AdministrativeLevel
from cosomis.mixins import PageMixin
from django.utils.translation import gettext_lazy as _


def _build_villages_data(admin_levels):
    villages = []
    for admin_level in admin_levels:
        uncompleted_tasks = 0
        first_phase = first_activity = first_task = None

        for phase in admin_level.phases.all().order_by("order"):
            for activity in phase.activities.all().order_by("order"):
                for task in activity.tasks.all().order_by("order"):
                    if task.status != Task.COMPLETED:
                        uncompleted_tasks += 1
                        if first_task is None:
                            first_phase = phase
                            first_activity = activity
                            first_task = task

        if uncompleted_tasks != 0:
            villages.append(
                {
                    'name': admin_level.name,
                    'uncompleted_tasks': uncompleted_tasks,
                    'id': admin_level.id,
                    'phase': first_phase.name if first_phase else '',
                    'activity': first_activity.name if first_activity else '',
                    'task': first_task.name if first_task else '',
                    'administrative_unit': admin_level.parent.name if admin_level.parent else '',
                }
            )
    return villages


class CddFunnelView(PageMixin, generic.ListView):
    template_name = "village_list.html"
    model = AdministrativeLevel
    title = _("CDD Funnel")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super(CddFunnelView, self).get_context_data(**kwargs)
        admin_levels = self.object_list.filter(type=AdministrativeLevel.VILLAGE)
        ctx['villages'] = _build_villages_data(admin_levels)
        return ctx


class CddFunnelCsvView(generic.View):
    def get(self, request, *args, **kwargs):
        admin_levels = AdministrativeLevel.objects.filter(type=AdministrativeLevel.VILLAGE)
        villages = _build_villages_data(admin_levels)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cdd_funnel.csv"'

        writer = csv.writer(response)
        writer.writerow([
            _('Name'),
            _('Uncompleted tasks'),
            _('Phase'),
            _('Activity'),
            _('Task'),
            _('Administrative Unit'),
        ])
        for village in villages:
            writer.writerow([
                village['name'],
                village['uncompleted_tasks'],
                village['phase'],
                village['activity'],
                village['task'],
                village['administrative_unit'],
            ])

        return response
