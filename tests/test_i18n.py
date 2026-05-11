from src.web.i18n import language_payload, normalize_language, translate


def test_supported_languages_and_fallbacks():
    payload = language_payload()

    assert payload["default"] == "zh"
    assert {"code": "zh", "label": "中文"} in payload["languages"]
    assert normalize_language("en") == "en"
    assert normalize_language("fr") == "zh"
    assert translate("insufficient_data", "en").startswith("Current detection data is insufficient")
    assert translate("missing.key", "zh") == "missing.key"
