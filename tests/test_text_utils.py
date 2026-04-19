from app.utils.text import detect_language, repair_mojibake, strip_html


def test_repair_mojibake_for_russian_text():
    broken = "Circle Ð·Ð°Ð¿ÑÑÑÐ¸Ð»Ð° USDC Bridge"
    assert "запустила" in repair_mojibake(broken).lower()


def test_strip_html_removes_tags():
    html = "<p>Hello <strong>world</strong></p>"
    assert strip_html(html) == "Hello world"


def test_detect_language_returns_ru_for_cyrillic():
    assert detect_language("Привет, рынок") == "ru"
