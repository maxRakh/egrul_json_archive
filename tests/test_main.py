import pytest

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



