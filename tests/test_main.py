import pytest

from main.main import *


def test_check_okved_valid_positive():
    assert not check_okved_valid(62)
    assert not check_okved_valid('62.02')


def test_check_okved_valid_negetive():
    with pytest.raises(ValueError):
        check_okved_valid(None)

    with pytest.raises(ValueError):
        check_okved_valid('InvalidOKVED')


def test_check_region_valid_positive():
    assert not check_region_valid('Москва')


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
    assert not select_by_main_okved('63.02', company_dict)
    assert not select_by_main_okved(63, company_dict)
    assert not select_by_main_okved('63', company_dict)


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
    assert not select_by_extra_okved(65, company_dict)
    assert not select_by_extra_okved('65', company_dict)
    assert not select_by_extra_okved('62.02.01', company_dict)
    assert not select_by_extra_okved(65, company_dict_empty)