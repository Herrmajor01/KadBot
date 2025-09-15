import os

from kadbot.crm.sync import extract_case_number


def test_extract_case_number_cyrillic():
    assert extract_case_number("Проект по делу А32-29491/2023") == "А32-29491/2023"


def test_extract_case_number_latin():
    assert extract_case_number("Case A12-3456/2021") == "A12-3456/2021"


def test_extract_case_number_absent():
    assert extract_case_number("Проект без номера") is None
