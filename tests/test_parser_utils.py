from datetime import datetime

from kadbot.kad.parser import parse_date


def test_parse_date_valid():
    d = parse_date("01.09.2023")
    assert isinstance(d, datetime)
    assert d.year == 2023 and d.month == 9 and d.day == 1


def test_parse_date_invalid():
    assert parse_date("2023-09-01") is None
    assert parse_date("") is None
    assert parse_date(None) is None  # type: ignore[arg-type]
