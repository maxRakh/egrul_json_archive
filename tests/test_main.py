import json
import os
import zipfile

import pytest
from pytest_mock import mocker

from main.main import *


def test_check_okved_valid_positive():
    assert check_okved_valid(62) is None
    assert check_okved_valid('62.02') is None


def test_check_okved_valid_negetive():
    with pytest.raises(ValueError):
        check_okved_valid(None)

    with pytest.raises(ValueError):
        check_okved_valid('InvalidOKVED')


def test_check_region_valid_positive():
    assert check_region_valid('Москва') is None


def test_check_region_valid_negative():
    with pytest.raises(ValueError):
        check_region_valid(None)

    with pytest.raises(ValueError):
        check_region_valid(546)


def test_select_by_main_okved_positive():
    company_dict = {
        'data': {
            'СвОКВЭД': {
                'СвОКВЭДОсн': {'КодОКВЭД': '62.02'}
            }
        }
    }
    assert select_by_main_okved('62.02', company_dict) == '62.02'
    assert select_by_main_okved(62, company_dict) == '62.02'
    assert select_by_main_okved('62', company_dict) == '62.02'


def test_select_by_main_okved_negative():
    company_dict = {
        'data': {
            'СвОКВЭД': {
                'СвОКВЭДОсн': {'КодОКВЭД': '62.02'}
            }
        }
    }
    assert select_by_main_okved('63.02', company_dict) is None
    assert select_by_main_okved(63, company_dict) is None
    assert select_by_main_okved('63', company_dict) is None


def test_select_by_extra_okved_positive():
    company_dict_with_list = {
        'data': {
            'СвОКВЭД': {
                'СвОКВЭДДоп': [
                    {'КодОКВЭД': '62.02'},
                    {'КодОКВЭД': '66.02'},
                ]
            }
        }
    }
    company_dict_with_dict = {
        'data': {
            'СвОКВЭД': {
                'СвОКВЭДДоп': {'КодОКВЭД': '62.02'}
            }
        }
    }
    assert select_by_extra_okved(62, company_dict_with_list) == '62.02'
    assert select_by_extra_okved(66, company_dict_with_list) == '66.02'
    assert select_by_extra_okved('62.02', company_dict_with_list) == '62.02'
    assert select_by_extra_okved('66.02', company_dict_with_list) == '66.02'
    assert select_by_extra_okved(62, company_dict_with_dict) == '62.02'
    assert select_by_extra_okved('62', company_dict_with_dict) == '62.02'


def test_select_by_extra_okved_negative():
    company_dict = {
        'data': {
            'СвОКВЭД': {
                'СвОКВЭДДоп': [
                    {'КодОКВЭД': '62.02'},
                    {'КодОКВЭД': '66.02'},
                ]
            }
        }
    }
    company_dict_empty = {
        'data': {
            'СвОКВЭД': {
            }
        }
    }
    assert select_by_extra_okved(65, company_dict) is None
    assert select_by_extra_okved('65', company_dict) is None
    assert select_by_extra_okved('62.02.01', company_dict) is None
    assert select_by_extra_okved(65, company_dict_empty) is None


def test_select_by_region_positive():
    company_dict = {
        'data': {'СвРегОрг': {'АдрРО': 'Москва ул. Полярная, д.2'}}
    }
    assert select_by_region('москва', company_dict)
    assert select_by_region('Москва', company_dict)


def test_select_by_region_negative():
    company_dict = {
        'data': {'СвРегОрг': {'АдрРО': 'Москва ул. Полярная, д.2'}}
    }
    assert select_by_region('тверь', company_dict) is False
    assert select_by_region('Тверь', company_dict) is False


def test_process_json_file_positive():
    test_data = [
        {
            "full_name": "Company A",
            "inn": "1234567890",
            "kpp": "987654321",
            "data": {
                "СвРегОрг": {
                    "АдрРО": "Хабаровск ул. Капитана д. 2"
                },
                'СвОКВЭД': {
                    'СвОКВЭДДоп': [
                        {'КодОКВЭД': '61.02'},
                        {'КодОКВЭД': '66.02'},
                    ]
                }
            }
        },
        {
            "full_name": "Company B",
            "okved": "62.02",
            "inn": "1234567899",
            "kpp": "987654322",
            "data": {
                "СвРегОрг": {
                    "АдрРО": "Москва ул. Врунгеля д. 2"
                },
                'СвОКВЭД': {
                    'СвОКВЭДДоп': [
                        {'КодОКВЭД': '62.02'},
                        {'КодОКВЭД': '66.02'},
                    ]
                }
            }
        }
    ]
    test_okved = '62'
    test_region = 'Москва'
    test_zip_file_path = 'test_data.zip'
    test_json_file = 'test_file.json'

    try:
        with zipfile.ZipFile(test_zip_file_path, 'w') as zip_file:
            zip_file.writestr(test_json_file, json.dumps(test_data))

        result = process_json_file(test_zip_file_path, test_okved, test_region, test_json_file)

        expected_result = [
            {
                'company_name': "Company B",
                'okved': "62.02",
                'inn': "1234567899",
                'kpp': "987654322",
                'legal_address': "Москва ул. Врунгеля д. 2"
            }
        ]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result == expected_result

    finally:
        if os.path.exists(test_zip_file_path):
            os.remove(test_zip_file_path)


def test_process_json_file_not_found_archive():
    invalid_archive_path = 'nonexistent.zip'
    with pytest.raises(FileNotFoundError):
        process_json_file(invalid_archive_path, '62', 'Москва', 'test_file.json')


def test_get_egrul_data_from_file_positive():
    test_data = [
        {
            "full_name": "Company A",
            "inn": "1234567890",
            "kpp": "987654321",
            "data": {
                "СвРегОрг": {
                    "АдрРО": "Хабаровск ул. Капитана д. 2"
                },
                'СвОКВЭД': {
                    'СвОКВЭДДоп': [
                        {'КодОКВЭД': '61.02'},
                        {'КодОКВЭД': '66.02'},
                    ]
                }
            }
        },
        {
            "full_name": "Company B",
            "okved": "62.02",
            "inn": "1234567899",
            "kpp": "987654322",
            "data": {
                "СвРегОрг": {
                    "АдрРО": "Москва ул. Врунгеля д. 2"
                },
                'СвОКВЭД': {
                    'СвОКВЭДДоп': [
                        {'КодОКВЭД': '62.02'},
                        {'КодОКВЭД': '66.02'},
                    ]
                }
            }
        }
    ]

    test_json_file = "test_file.json"
    test_archive_path = "test_archive.zip"
    expected_result = [
        {
            'company_name': "Company B",
            'okved': "62.02",
            'inn': "1234567899",
            'kpp': "987654322",
            'legal_address': "Москва ул. Врунгеля д. 2"
        }
    ]

    try:
        with zipfile.ZipFile(test_archive_path, 'w') as zip_file:
            zip_file.writestr(test_json_file, json.dumps(test_data))

        result = get_egrul_data_from_file(test_archive_path, '62', 'Москва')
        assert result == expected_result
        assert isinstance(result, list)
        assert len(result) == 1
    finally:
        if os.path.exists(test_archive_path):
            os.remove(test_archive_path)


def test_get_egrul_data_from_file_not_found_archive():
    invalid_archive_path = 'nonexistent.zip'
    with pytest.raises(FileNotFoundError):
        get_egrul_data_from_file(invalid_archive_path, '62', 'Москва')


