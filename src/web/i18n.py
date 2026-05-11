from __future__ import annotations


SUPPORTED_LANGUAGES = (
    {"code": "zh", "label": "中文"},
    {"code": "en", "label": "English"},
)
DEFAULT_LANGUAGE = "zh"

TRANSLATIONS = {
    "zh": {
        "insufficient_data": "当前检测数据不足，建议继续观察或人工复核。",
        "analysis_failed": "分析失败，请稍后重试。",
    },
    "en": {
        "insufficient_data": "Current detection data is insufficient; continue observing or request manual review.",
        "analysis_failed": "Analysis failed. Please try again later.",
    },
}


def normalize_language(language: str | None) -> str:
    codes = {item["code"] for item in SUPPORTED_LANGUAGES}
    return language if language in codes else DEFAULT_LANGUAGE


def translate(key: str, language: str | None = None) -> str:
    lang = normalize_language(language)
    return TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key) or key


def language_payload() -> dict[str, object]:
    return {"default": DEFAULT_LANGUAGE, "languages": list(SUPPORTED_LANGUAGES)}
