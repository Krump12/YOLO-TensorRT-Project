from __future__ import annotations

from src.web.i18n import normalize_language, translate
from src.web.storage import WebStorage


def build_chat_evidence(
    detections: list[dict[str, object]],
    analyses: list[dict[str, object]],
) -> dict[str, object]:
    class_counts: dict[str, int] = {}
    for detection in detections:
        class_name = str(detection["class_name"])
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
    return {
        "detection_count": len(detections),
        "analysis_count": len(analyses),
        "class_counts": class_counts,
        "analysis_summaries": [
            {
                "analysis_id": item["analysis_id"],
                "severity": item["severity"],
                "conclusion": item["conclusion"],
                "pest_or_disease_name": item.get("pest_or_disease_name"),
            }
            for item in analyses[:5]
        ],
    }


class AgentChatService:
    def __init__(self, storage: WebStorage) -> None:
        self.storage = storage

    def answer(self, *, user_id: str, question: str, language: str = "zh", hours: int = 48) -> dict[str, object]:
        lang = normalize_language(language)
        detections = self.storage.recent_detections(hours=hours)
        analyses = self.storage.recent_analysis(hours=hours)
        evidence = build_chat_evidence(detections, analyses)
        related_detection_ids = [str(item["detection_id"]) for item in detections[:10]]
        related_analysis_ids = [str(item["analysis_id"]) for item in analyses[:10]]
        if not detections and not analyses:
            answer = translate("insufficient_data", lang)
        else:
            class_counts = evidence["class_counts"]
            top_class = max(class_counts, key=class_counts.get) if class_counts else None
            highest = analyses[0] if analyses else None
            if lang == "en":
                answer = (
                    f"Conclusion: recent evidence contains {len(detections)} target detections"
                    f"{' and the most frequent class is ' + top_class if top_class else ''}. "
                    f"Basis: {len(analyses)} saved analysis result(s) and recent detection records. "
                    "Recommendation: review cited records and perform manual confirmation before treatment. "
                    "Uncertainty: automated detections may include false positives."
                )
            else:
                answer = (
                    f"结论：最近数据包含 {len(detections)} 条有目标检测"
                    f"{'，出现最多的类别是 ' + top_class if top_class else ''}。"
                    f"数据依据：{len(analyses)} 条分析结果和最近检测记录。"
                    "建议措施：查看相关记录并在处理前进行人工复核。"
                    "不确定性：自动检测可能存在误检。"
                )
            if highest:
                answer += f" Analysis: {highest['conclusion']}"
        return self.storage.save_chat_message(
            user_id=user_id,
            question=question,
            answer=answer,
            evidence=evidence,
            related_detection_ids=related_detection_ids,
            related_analysis_ids=related_analysis_ids,
            language=lang,
        )
