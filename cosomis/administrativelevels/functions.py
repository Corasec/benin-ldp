import logging
import pandas as pd
from administrativelevels.models import AdministrativeLevel
from cosomis.constants import ADMINISTRATIVE_LEVEL_TYPE


def conversion_file_csv_to_dict(file_csv, sheet="Sheet1") -> dict:
    read_file = pd.read_csv(file_csv, sheet)
    datas = read_file.to_dict()

    return datas

def conversion_file_xlsx_to_dict(file_xlsx, sheet="Sheet1") -> dict:
    read_file = pd.read_excel(file_xlsx, sheet)
    datas = read_file.to_dict()

    return datas

def save_adm_lvl_csv_datas_to_db(datas_file) -> str:
    """Function to save administrative levels CSV datas in the database"""
    datas_file = conversion_file_xlsx_to_dict(datas_file)

    logger = logging.getLogger(__name__)

    columns = list(ADMINISTRATIVE_LEVEL_TYPE.constants.keys())
    if datas_file:
        num_rows = len(next(iter(datas_file.values())))
        saved_count = 0
        error_count = 0

        # save column by column
        for column in columns:
            for count, _ in enumerate(range(num_rows)):
                try:
                    name = str(datas_file[column][count]).upper().strip()

                    _type = "Unknown"
                    parent_type = ()
                    if column == ADMINISTRATIVE_LEVEL_TYPE.DÉPARTEMENT.constant:
                        _type = ADMINISTRATIVE_LEVEL_TYPE.DÉPARTEMENT
                    elif column == ADMINISTRATIVE_LEVEL_TYPE.COMMUNE.constant:
                        _type = ADMINISTRATIVE_LEVEL_TYPE.COMMUNE
                        parent_type = ADMINISTRATIVE_LEVEL_TYPE.DÉPARTEMENT
                    elif column == ADMINISTRATIVE_LEVEL_TYPE.ARRONDISSEMENT.constant:
                        _type = ADMINISTRATIVE_LEVEL_TYPE.ARRONDISSEMENT
                        parent_type = ADMINISTRATIVE_LEVEL_TYPE.COMMUNE
                    elif column == ADMINISTRATIVE_LEVEL_TYPE.VILLAGE.constant:
                        _type = ADMINISTRATIVE_LEVEL_TYPE.VILLAGE
                        parent_type = ADMINISTRATIVE_LEVEL_TYPE.ARRONDISSEMENT

                    parent = None
                    print(f"(type, parent_type) : ({_type}{parent_type})")
                    try:
                        if _type not in (
                            ADMINISTRATIVE_LEVEL_TYPE.DÉPARTEMENT,
                            "Unknown",
                        ):
                            parent = AdministrativeLevel.objects.filter(
                                name=str(datas_file[parent_type.constant][count])
                                .upper()
                                .strip(),
                                type=parent_type.value,
                            ).first()
                            print(f"(parent_name) : {parent.name}")
                    except Exception as exc:
                        logger.exception(exc)
                    print(f"(adm, parent) : ({name}_{_type},p_{parent_type})")
                    admlvl, created = AdministrativeLevel.objects.get_or_create(
                        name=name, type=_type, parent=parent
                    )
                    if created:
                        saved_count += 1

                except Exception as exc:
                    error_count += 1
                    logger.exception(f"Exception occurred for {admlvl} : {exc}")

        if saved_count > 0 and error_count == 0:
            message = "Success!"
        elif saved_count == 0 and error_count == 0:
            message = "No items have been saved!"
        elif saved_count == 0 and error_count > 0:
            message = "A problem has occurred!"
        else:
            message = "Some element(s) have not been saved!"

        return message