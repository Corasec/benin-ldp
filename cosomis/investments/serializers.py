from rest_framework import serializers

from investments.models import Investment
from django.utils.translation import gettext_lazy as _


class InvestmentSerializer(serializers.ModelSerializer):

    select_input = serializers.SerializerMethodField()
    administrative_level__type = serializers.SerializerMethodField()
    administrative_level__name = serializers.SerializerMethodField()
    administrative_level__parent__name = serializers.SerializerMethodField()
    administrative_level__parent__parent__name = serializers.SerializerMethodField()
    administrative_level__parent__parent__parent__name = serializers.SerializerMethodField()
    population_priority = serializers.SerializerMethodField()


    class Meta:
        model = Investment
        fields = '__all__'

    def get_select_input(self, obj):
        if self.__is_unfunded_and_available(obj):
            return '<input class="project-table-check" id="checkbox-' + str(obj.id) + '" value="' + str(obj.id) + '" type="checkbox" disabled title="'+ _("The project does not have enough funds. The project has ") + str(self.context['project_total_fund']) + ' FCFA">'
        if self.__is_funded(obj):
            return '<input class="project-table-check" id="checkbox-' + str(obj.id) + '" value="' + str(obj.id) + '" type="checkbox" checked disabled title="'+ _("This investment is already funded by the project") + '">'
        if 'all_queryset' in self.context and self.context['all_queryset'] == 'false':
            return '<input class="project-table-check" id="checkbox-' + str(obj.id) + '" value="' + str(obj.id) + '" type="checkbox">'
        if self.__is_already_funded_by_other(obj):
            return '<input class="project-table-check" id="checkbox-' + str(obj.id) + '" value="' + str(
                obj.id) + '" type="checkbox" disabled title="'+ _("This investment is already funded by other project") + '">'

        return '<input class="project-table-check" id="checkbox-' + str(obj.id) + '" value="' + str(obj.id) + '" type="checkbox" checked>'

    def __is_funded(self, obj):
        return ('project_id' in self.context and self.context['project_id'] is not None
                and obj.funded_by is not None and obj.funded_by.id == self.context['project_id'])

    def __is_already_funded_by_other(self, obj):
        return ('project_id' in self.context and self.context['project_id'] is not None
                and obj.funded_by is not None and obj.funded_by.id != self.context['project_id'])
    def __is_unfunded_and_available(self, obj):
        return ('project_total_fund' in self.context and self.context['project_total_fund'] is not None
                and self.context['project_total_fund'] <= obj.estimated_cost) is True and obj.funded_by is None
    def get_administrative_level__type(self, obj):
        return obj.administrative_level.type

    def get_administrative_level__name(self, obj):
        return obj.administrative_level.name

    def get_administrative_level__parent__name(self, obj):
        return obj.administrative_level.parent.name

    def get_administrative_level__parent__parent__name(self, obj):
        return obj.administrative_level.parent.parent.name

    def get_administrative_level__parent__parent__parent__name(self, obj):
        return obj.administrative_level.parent.parent.parent.name

    def get_population_priority(self, obj):
        population_priority = list()
        if obj.endorsed_by_youth:
            population_priority.append('J')
        if obj.endorsed_by_women:
            population_priority.append('F')
        if obj.endorsed_by_agriculturist:
            population_priority.append('AG')
        if obj.endorsed_by_pastoralist:
            population_priority.append('ME')
        return ', '.join(population_priority)

