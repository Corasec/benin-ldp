from django.core.management.base import BaseCommand
from no_sql_client import NoSQLClient
from administrativelevels.models import AdministrativeLevel


class Command(BaseCommand):
    help = 'Syncs the facilitator of an administrative level'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.nsc = NoSQLClient()
        db = self.nsc.get_db('administrative_levels')
        selector = {
            "type": "administrative_level"
        }
        docs = db.get_query_result(selector)
        for document in docs:
            create_or_update_adm(document)
            recursive_administrative_level(document, db)
        self.stdout.write(self.style.SUCCESS('Successfully executed syncfacilitator'))


def recursive_administrative_level(administrative_level, database):
    print(
        administrative_level['name'],
        administrative_level['administrative_level'],
        administrative_level['administrative_id']
    )
    selector = {
        "type": "administrative_level",
        "parent_id": administrative_level['administrative_id']
    }
    docs = database.get_query_result(selector)
    for document in docs:
        create_or_update_adm(document)
        recursive_administrative_level(document, database)


def create_or_update_adm(administrative_level_data):
    adm_id = administrative_level_data.get('administrative_id')
    adm_name = administrative_level_data.get('name')
    adm_parent_id = administrative_level_data.get('parent_id')
    adm_type = administrative_level_data.get('administrative_level')
    try:
        adm_level = AdministrativeLevel.objects.get(no_sql_db_id=adm_id)
        adm_level.name = adm_name
        adm_level.type = adm_type
        adm_level.facilitator = ''
        if adm_parent_id:
            parent = AdministrativeLevel.objects.get(no_sql_db_id=adm_parent_id)
            adm_level.parent = parent
        adm_level.save()
    except AdministrativeLevel.DoesNotExist:
        parent = None
        if adm_parent_id:
            parent = AdministrativeLevel.objects.get(no_sql_db_id=adm_parent_id)
        adm_level = AdministrativeLevel(
            no_sql_db_id=adm_id,
            name=adm_name,
            parent=parent,
            type=adm_type,
            facilitator=''
        )
        adm_level.save()
