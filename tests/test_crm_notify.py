import os

from kadbot.config import reset_config
from kadbot.crm.notify import build_comment_text


def test_build_comment_text_escapes_and_defaults(monkeypatch):
    monkeypatch.setenv("USERID", "123")
    monkeypatch.setenv("USER_NAME", "Иван & Ко")
    monkeypatch.setenv("ASPRO_API_KEY", "dummy")
    monkeypatch.setenv("ASPRO_COMPANY", "dummyco")
    reset_config()

    html_text = build_comment_text("<Событие>", "01.01.2024", None)
    assert "&lt;Событие&gt;" in html_text
    assert "Дата: 01.01.2024" in html_text
    assert "Иван &amp; Ко" in html_text
    assert "href='#'" in html_text
