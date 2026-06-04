from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from app.labels import DISEASE_GUIDANCE, LABEL_MAP, MEDICAL_DISCLAIMER


def _default_model_dir() -> Path:
    env_dir = os.getenv("MODEL_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "skin-disease-classifier").resolve()


@lru_cache(maxsize=1)
def load_model_bundle(model_dir: Optional[str] = None) -> Dict[str, Any]:
    resolved = Path(model_dir).expanduser().resolve() if model_dir else _default_model_dir()
    processor = AutoImageProcessor.from_pretrained(str(resolved), local_files_only=True)
    model = AutoModelForImageClassification.from_pretrained(str(resolved), local_files_only=True)
    model.eval()
    return {"processor": processor, "model": model, "model_dir": resolved}


def predict_image(image: Image.Image, top_k: int = 3, model_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    bundle = load_model_bundle(model_dir)
    processor = bundle["processor"]
    model = bundle["model"]
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    id2label = model.config.id2label
    k = min(top_k, probs.shape[-1])
    values, indices = torch.topk(probs, k=k)
    results = []
    for score, idx in zip(values.tolist(), indices.tolist()):
        code = id2label.get(idx, str(idx))
        guidance = DISEASE_GUIDANCE.get(code, {})
        results.append(
            {
                "code": code,
                "label": LABEL_MAP.get(code, code),
                "score": float(score),
                "diagnosis": guidance.get("diagnosis", LABEL_MAP.get(code, code)),
                "overview": guidance.get("overview", ""),
                "advice": guidance.get("advice", []),
                "warning_signs": guidance.get("warning_signs", []),
            }
        )
    return results


def _symptom_weight(symptoms: Dict[str, Any]) -> float:
    yes = {"yes", True, "true", "1", 1}
    weights = {
        "itch": 0.10,
        "bleed": 0.25,
        "grow": 0.20,
        "pain": 0.12,
        "change": 0.18,
    }
    total = 0.0
    for key, weight in weights.items():
        value = symptoms.get(key, "no")
        if isinstance(value, str):
            value = value.strip().lower()
        if value in yes:
            total += weight
    return min(total, 0.6)


def _priority_from_score(label_code: str, confidence: float, red_flag_score: float) -> Dict[str, str]:
    high_risk = {"MEL", "SCC", "BCC"}
    combined = confidence * 0.65 + red_flag_score
    if label_code in high_risk and combined >= 0.55:
        return {
            "priority": "urgent",
            "risk_level": "high",
            "risk_reason": "Mô hình và triệu chứng đều gợi ý cần ưu tiên đánh giá sớm.",
            "recommendation": "Có dấu hiệu cần được bác sĩ da liễu xem lại sớm.",
        }
    if combined >= 0.38:
        return {
            "priority": "review",
            "risk_level": "moderate",
            "risk_reason": "Có một số dấu hiệu cần theo dõi và đánh giá lại.",
            "recommendation": "Nên lưu ảnh và đặt lịch xem lại, đặc biệt nếu tổn thương đang thay đổi.",
        }
    return {
        "priority": "monitor",
        "risk_level": "low",
        "risk_reason": "Kết quả hiện tại chưa cho thấy dấu hiệu nguy cơ cao.",
        "recommendation": "Tạm thời có thể theo dõi thêm, chụp lại khi có thay đổi rõ ràng.",
    }


def screen_image(
    image: Image.Image,
    *,
    symptoms: Dict[str, Any],
    top_k: int = 3,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    predictions = predict_image(image, top_k=top_k, model_dir=model_dir)
    top = predictions[0]
    red_flag_score = _symptom_weight(symptoms)
    priority_data = _priority_from_score(top["code"], float(top["score"]), red_flag_score)
    guidance = DISEASE_GUIDANCE.get(top["code"], {})
    return {
        "predicted_code": top["code"],
        "predicted_label": top["label"],
        "diagnosis_summary": guidance.get("diagnosis", top["label"]),
        "condition_overview": guidance.get("overview", ""),
        "care_advice": guidance.get("advice", []),
        "warning_signs": guidance.get("warning_signs", []),
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "confidence": float(top["score"]),
        "red_flag_score": red_flag_score,
        "priority": priority_data["priority"],
        "risk_level": priority_data["risk_level"],
        "risk_reason": priority_data["risk_reason"],
        "recommendation": priority_data["recommendation"],
        "symptoms": symptoms,
        "predictions": predictions,
    }


def load_image(path: str) -> Image.Image:
    return Image.open(path)
