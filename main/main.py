import json
import os
import re
import zipfile
import logging.config
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import List, Optional, Union

import psycopg2
from dotenv import load_dotenv

from config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)
logging.config.dictConfig(DEFAULT_CONFIG)

load_dotenv()

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')


def check_okved_valid(okved_for_check: Union[str, int]) -> None:
    """Проверяет ОКВЭД на валидность"""
    pattern = re.compile(r'^\d{2}(\.\d{2}(\.\d{1,2})?)?$')
    if not okved_for_check:
        raise ValueError('Необходимо ввести ОКВЭД')
    if not pattern.match(str(okved_for_check)):
        raise ValueError(
            'Необходимо правильно ввести группировку или конкретный ОКВЭД'
        )


def check_region_valid(region_for_check: str) -> None:
    """Проверяет код региона на валидность."""
    if not region_for_check:
        raise ValueError('Необходимо ввести название города/региона')
    if not isinstance(region_for_check, str):
        raise ValueError('Название города/региона должно быть строкой.')


def select_by_main_okved(
        okved: Union[str, int], checking_company_dict: dict
) -> Optional[str]:
    """
    Проверяет словарь с компанией подходит ли основной ОКВЭД по группе ОКВЭД
    и в случае успеха возвращет его
    """
    pattern = fr'^{re.escape(str(okved))}'
    code_okved = checking_company_dict.get(
        'data', {}).get('СвОКВЭД', {}).get('СвОКВЭДОсн', {}).get('КодОКВЭД', '')
    if re.match(pattern, code_okved):
        return code_okved


def select_by_extra_okved(
        okved: Union[str, int], checking_company_dict: dict
) -> Optional[str]:
    """
    Проверяет словарь с компанией подходит ли дополнительный ОКВЭД
    по группе ОКВЭД и в случае успеха возвращет его
    """
    pattern = fr'^{re.escape(str(okved))}'
    extra_okved_list = checking_company_dict.get(
        'data', {}).get('СвОКВЭД', {}).get('СвОКВЭДДоп', {})

    checking_code = None
    if extra_okved_list:
        if isinstance(extra_okved_list, list):
            for code_okved in extra_okved_list:
                if code_okved and re.match(pattern, code_okved.get('КодОКВЭД')):
                    checking_code = code_okved.get('КодОКВЭД')
        elif isinstance(extra_okved_list, dict) \
                and re.match(pattern, extra_okved_list.get('КодОКВЭД')):
            checking_code = extra_okved_list.get('КодОКВЭД')

    if checking_code:
        return checking_code


def select_by_region(region_name: str, checking_company_dict: dict) -> bool:
    """
    Проверяет словарь с компанией подходит ли он по заданному городу/региону
    """
    return region_name.title() in (checking_company_dict.get(
        'data').get('СвРегОрг', {}).get('АдрРО', '')).split()


def process_json_file(
        file_path: str, okved: Union[str, int], region: str, file_info
) -> Optional[list]:
    """Обрабатывает json файл в архиве и если компания из файла подходит
    пораметрам добавляет словарь с компанией в список.
    После завершения обработки файла возвращает список со словарями с компаниями
    заданных параметров"""

    results = []

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            with zip_ref.open(file_info, 'r') as json_file:
                json_content = json.load(json_file)

                for company_dict in json_content:
                    check_main_okved = select_by_main_okved(
                        okved, company_dict)
                    check_extra_okved = select_by_extra_okved(
                        okved, company_dict)

                    if (check_main_okved or
                        check_extra_okved) and select_by_region(
                            region, company_dict):
                        new_comp = {
                            'company_name': company_dict.get('full_name'),
                            'okved': check_main_okved if check_main_okved
                            else check_extra_okved,
                            'inn': company_dict.get('inn'),
                            'kpp': company_dict.get('kpp'),
                            'legal_address': company_dict.get(
                                'data').get('СвРегОрг').get('АдрРО')
                        }
                        results.append(new_comp)

        if results:
            return results
    except FileNotFoundError as ex:
        logger.error(f'Указанный файл не найден: {ex}')
    except zipfile.BadZipFile as ex:
        logger.error(f'Проблема с архивом: {ex}')
    except Exception as ex:
        logger.error(f'Проблема с обработкой файла: {ex}')


def get_egrul_data_from_file(
        file_path: str, okved_group: Union[str, int], region: str
) -> Optional[list]:
    """
    Получает список словарей с компаниями из архива по заданным ОКВЭД и региону.
    Параллельно проверяет все json файлы в архиве, используя библиотеку
    multiprocessing после чего возвращает список словарей с компаниями
    в соотвествии с заданными параметрами.
    """
    check_okved_valid(okved_group)
    check_region_valid(region)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            json_files = [file_info for file_info in zip_ref.infolist()
                          if file_info.filename.endswith('.json')]

        with Pool((cpu_count())) as pool:
            results = pool.starmap(
                process_json_file, [(file_path, okved_group, region, file_info
                                     ) for file_info in json_files])

        return [
            item for sublist in results if sublist for item in sublist if item
        ]

    except FileNotFoundError as ex:
        logger.error(f'Указанный файл не найден: {ex}')
    except zipfile.BadZipFile as ex:
        logger.error(f'Проблема с архивом: {ex}')
    except Exception as ex:
        logger.error(f'Проблема с обработкой файла: {ex}')


def insert_data_to_database(companies_data: List[dict]) -> None:
    """
    Создает таблицу в БД, если она не существует и вносит в нее полученные
    из файла данные.
    """
    try:
        with psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        ) as con:
            with con.cursor() as cur:
                cur.execute('''CREATE TABLE IF NOT EXISTS companies(
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255),
                    okved VARCHAR(155),
                    inn VARCHAR(10),
                    kpp VARCHAR(10),
                    legal_address VARCHAR(255)
                    );''')

                logger.info('Таблица создана успешно.')

                for company in companies_data:
                    company_name = company.get('company_name')
                    okved_comp = company.get('okved')
                    inn = company.get('inn')
                    kpp = company.get('kpp')
                    legal_address = company.get('legal_address')

                    cur.execute(
                        "INSERT INTO companies "
                        "(company_name, okved, inn, kpp, legal_address) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (company_name, okved_comp, inn, kpp, legal_address)
                    )
                con.commit()
                logger.info("Записи внесены в БД успешно.")
    except psycopg2.Error as ex:
        logger.error(f"DataBase Error: {ex}")


def main():
    """
    Приложение для получения сведений по компаниям в соотвествии с заданным
    списком ОКВЭД и регионом из архивированного файла.
    В случае успешного получения данных, эти сведения (название компании,
    код ОКВЭД, ИНН, КПП и место регистрации ЮЛ) вносятся в базу данных
    PostgreSQL.

    Параметры:
    - okved: Группировка ОКВЭД или конкретный ОКВЭД, по которым осуществляется
    фильтрация компаний.
    - region: Название города или региона, по которому осуществляется фильтрация
    компаний.
    - file_path: Путь к архивированному JSON-файлу, содержащему данные
    о компаниях.
    """
    okved = 62
    region = 'Хабаровск'
    file_path = '/Users/maxr/Downloads/egrul.json.zip'

    logger.info('Начало работы приложения.')
    data = get_egrul_data_from_file(
        file_path=file_path, okved_group=okved, region=region
    )

    if data:
        insert_data_to_database(data)
    else:
        logger.warning("Компаний по заданным параметрам не найдено.")
    logger.info('Окончание работы приложения')


if __name__ == '__main__':
    start_time = datetime.now()

    main()
    logger.info(f'Время работы программы: {datetime.now() - start_time}')
