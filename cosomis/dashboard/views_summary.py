from django.conf import settings
from django.views import generic
from django.utils.translation import gettext_lazy as _
from cosomis.mixins import LoginRequiredApproveRequiredMixin
from usermanager.models import Organization
from administrativelevels.models import AdministrativeLevel, Sector, Category
from investments.models import Investment  # Make sure to import the Investment model


class DashboardSummaryView(LoginRequiredApproveRequiredMixin, generic.TemplateView):
    template_name = "dashboard_summary.html"
    active_level1 = 'dashboard_summary'
    title = _('Dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['access_token'] = settings.MAPBOX_ACCESS_TOKEN
        context['lat'] = settings.DIAGNOSTIC_MAP_LATITUDE
        context['lng'] = settings.DIAGNOSTIC_MAP_LONGITUDE
        context['zoom'] = settings.DIAGNOSTIC_MAP_ZOOM
        context['ws_bound'] = settings.DIAGNOSTIC_MAP_WS_BOUND
        context['en_bound'] = settings.DIAGNOSTIC_MAP_EN_BOUND
        context['country_iso_code'] = settings.DIAGNOSTIC_MAP_ISO_CODE
        context.update(self.get_filters_context())
        context['project_statuses'] = Investment.PROJECT_STATUS_CHOICES
        return context

    def get_filters_context(self):
        filters_context = {}
        adm_queryset = AdministrativeLevel.objects.all()

        filters_context["countries"] = adm_queryset.filter(type=AdministrativeLevel.COUNTRY)
        filters_context["departments"] = adm_queryset.filter(type=AdministrativeLevel.DEPARTMENTS)
        filters_context["communes"] = adm_queryset.filter(type=AdministrativeLevel.COMMUNE)
        filters_context["cities"] = adm_queryset.filter(type=AdministrativeLevel.CITY)
        filters_context["villages"] = adm_queryset.filter(type=AdministrativeLevel.VILLAGE)
        filters_context["organizations"] = Organization.objects.all()
        filters_context["sectors"] = Category.objects.all()
        filters_context["types"] = Investment.INVESTMENT_STATUS_CHOICES

        if "country-filter" in self.request.GET:
            filters_context["departments"] = filters_context["departments"].filter(
                parent__id=self.request.GET["country-filter"]
            )

        if "department-filter" in self.request.GET:
            filters_context["communes"] = filters_context["communes"].filter(
                parent__id=self.request.GET["department-filter"]
            )

        if "commune-filter" in self.request.GET:
            filters_context["cities"] = filters_context["cities"].filter(
                parent__id=self.request.GET["commune-filter"]
            )

        if "city-filter" in self.request.GET:
            filters_context["villages"] = filters_context["villages"].filter(
                parent__id=self.request.GET["city-filter"]
            )

        filters_context["query_strings_raw"] = self.request.GET.copy()

        filters_context["subpopulations"] = [
            {"id": "endorsed_by_youth", "name": _("Endorsed by youth")},
            {"id": "endorsed_by_women", "name": _("Endorsed by women")}
        ]
        return filters_context
