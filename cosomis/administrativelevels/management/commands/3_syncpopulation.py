from django.core.management.base import BaseCommand
from no_sql_client import NoSQLClient
from administrativelevels.models import AdministrativeLevel

class Command(BaseCommand):
    help = 'Description of your command'

    def check_for_valid_facilitator(self, facilitator):
        db = self.nsc.get_db(facilitator).get_query_result({
            "type": "facilitator"
        })
        for document in db:
            print("Facilitator", document)
            try:
                if not document['develop_mode'] and not document["training_mode"]:
                    print("Facilitator is valid", document)
                    return True
            except:
                return False
        return False

    def handle(self, *args, **options):
        # Your command logic here
        self.nsc = NoSQLClient()
        facilitator_dbs = self.nsc.list_all_databases('facilitator')
        for db_name in facilitator_dbs:
            if self.check_for_valid_facilitator(db_name):
                db = self.nsc.get_db(db_name).get_query_result({
                    "type": "task",
                    "phase_name": "Préparation",
                    "name": "Première réunion au niveau  communale (à la Mairie) - Présentation de l'équipe et du projet COSO aux autorités",
                })
                for document in db:
                    update_or_create_adm_document(self.nsc, document)
        self.stdout.write(self.style.SUCCESS('Successfully executed mycommand!'))

def update_or_create_adm_document(client, population_document):

    # Access the 'purs_test' database

    # Extract the administrative_level_id from the priorities document
    adm_id = population_document['administrative_level_id']

    # Check if a document with the given adm_id exists in the 'purs_test' database
    selector = {
        "adm_id": adm_id,
        "type": "administrative_level"
    }
    # docs = Result(db.all_docs, include_docs=True, selector=selector).all()

    adm_object = AdministrativeLevel.objects.get(no_sql_db_id=adm_id)

    extracted_population_data = None

    # Extract priorities from the priorities document
    if 'form_response' in population_document:
        if population_document.get('form_response'):
            extracted_population_data = extract_population_data(population_document['form_response'])

    if not extracted_population_data:
        return

    # If the document exists, update it
    if adm_object:
        adm_object.total_population = extracted_population_data['total_population']
        adm_object.population_men = extracted_population_data['population_men']
        adm_object.population_women = extracted_population_data['population_women']
        adm_object.population_young = extracted_population_data['population_young']
        adm_object.population_elder = extracted_population_data['population_elder']
        adm_object.population_handicap = extracted_population_data['population_handicap']
        adm_object.population_agriculture = extracted_population_data['population_agriculture']
        adm_object.population_breeders = extracted_population_data['population_breeders']
        adm_object.population_minorities = extracted_population_data['population_minorities']
        adm_object.save()


def extract_population_data(form_response):
    extracted_population_data = {
        "total_population": 0,
        "population_men": 0,
        "population_women": 0,
        "population_young": 0,
        "population_elder": 0,
        "population_handicap": 0,
        "population_agriculture": 0,
        "population_breeders": 0,
        "population_minorities": 0
    }

    for entry in form_response:
        extracted_population_data["population_men"] = entry.get("totalHommes", 0)
        extracted_population_data["population_women"] = entry.get("totalFemmes", 0)

    print('here is the result:', extracted_population_data)
    return extracted_population_data
