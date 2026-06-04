from __future__ import annotations

import io
import os
from typing import Dict, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from PIL import Image

from app.ledger import append_prediction, export_chain_csv, export_chain_json, get_chain, get_chain_summary, validate_chain
from app.model import load_model_bundle, predict_image, screen_image
from app.schemas import LedgerResponse, LedgerValidateResponse, PredictionBlockItem, PredictionItem, PredictionResponse, ScreenResponse
from app.web import render_homepage, render_ledger_page


app = FastAPI(title="Skin Disease Screening App", version="1.2.0")


@app.get("/health")
def health() -> Dict[str, str]:
    bundle = load_model_bundle()
    return {"status": "ok", "model_dir": str(bundle["model_dir"])}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    bundle = load_model_bundle()
    blocks = get_chain(limit=5)
    summary = get_chain_summary()
    validation = validate_chain()
    return HTMLResponse(
        content=render_homepage(
            model_dir=str(bundle["model_dir"]),
            ledger_blocks=blocks,
            ledger_validation=validation,
            ledger_summary=summary,
        )
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...), top_k: Optional[int] = None) -> PredictionResponse:
    bundle = load_model_bundle()
    raw = await file.read()
    image = Image.open(io.BytesIO(raw))
    effective_top_k = top_k or int(os.getenv("TOP_K", "3"))
    predictions = predict_image(image, top_k=effective_top_k)
    return PredictionResponse(
        model_dir=str(bundle["model_dir"]),
        top_k=effective_top_k,
        predictions=[PredictionItem(**item) for item in predictions],
    )


@app.post("/screen", response_model=ScreenResponse)
async def screen(
    file: UploadFile = File(...),
    itch: str = Form("no"),
    bleed: str = Form("no"),
    grow: str = Form("no"),
    pain: str = Form("no"),
    change: str = Form("no"),
    top_k: int = Form(3),
) -> ScreenResponse:
    bundle = load_model_bundle()
    raw = await file.read()
    image = Image.open(io.BytesIO(raw))
    symptoms = {
        "itch": itch,
        "bleed": bleed,
        "grow": grow,
        "pain": pain,
        "change": change,
    }
    result = screen_image(image, symptoms=symptoms, top_k=top_k)
    append_prediction(
        source="api-diagnosis",
        image_name=file.filename or "uploaded-image",
        image_bytes=raw,
        model_dir=str(bundle["model_dir"]),
        top_k=top_k,
        predictions=result["predictions"],
    )
    return ScreenResponse(
        model_dir=str(bundle["model_dir"]),
        top_k=top_k,
        predicted_code=result["predicted_code"],
        predicted_label=result["predicted_label"],
        diagnosis_summary=str(result.get("diagnosis_summary", "")),
        condition_overview=str(result.get("condition_overview", "")),
        care_advice=list(result.get("care_advice", [])),
        warning_signs=list(result.get("warning_signs", [])),
        medical_disclaimer=str(result.get("medical_disclaimer", "")),
        confidence=float(result["confidence"]),
        red_flag_score=float(result["red_flag_score"]),
        priority=str(result["priority"]),
        risk_level=str(result["risk_level"]),
        risk_reason=str(result["risk_reason"]),
        recommendation=str(result["recommendation"]),
        symptoms=symptoms,
        predictions=[PredictionItem(**item) for item in result["predictions"]],
    )


@app.post("/screen-ui", response_class=HTMLResponse)
async def screen_ui(
    file: UploadFile = File(...),
    itch: str = Form("no"),
    bleed: str = Form("no"),
    grow: str = Form("no"),
    pain: str = Form("no"),
    change: str = Form("no"),
    top_k: int = Form(3),
) -> HTMLResponse:
    bundle = load_model_bundle()
    try:
        raw = await file.read()
        image = Image.open(io.BytesIO(raw))
        symptoms = {
            "itch": itch,
            "bleed": bleed,
            "grow": grow,
            "pain": pain,
            "change": change,
        }
        result = screen_image(image, symptoms=symptoms, top_k=top_k)
        append_prediction(
            source="web-diagnosis",
            image_name=file.filename or "uploaded-image",
            image_bytes=raw,
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            predictions=result["predictions"],
        )
        html = render_homepage(
            screen=result,
            predictions=result["predictions"],
            uploaded_image=raw,
            uploaded_mime_type=file.content_type or "image/jpeg",
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            ledger_blocks=get_chain(limit=5),
            ledger_validation=validate_chain(),
            ledger_summary=get_chain_summary(),
        )
        return HTMLResponse(content=html)
    except Exception as exc:
        return HTMLResponse(
            content=render_homepage(
                model_dir=str(bundle["model_dir"]),
                top_k=top_k,
                error=f"Không thể xử lý ảnh: {exc}",
                ledger_blocks=get_chain(limit=5),
                ledger_validation=validate_chain(),
                ledger_summary=get_chain_summary(),
            ),
            status_code=400,
        )


@app.get("/ledger", response_model=LedgerResponse)
def ledger(limit: int = 20) -> LedgerResponse:
    blocks = get_chain(limit=limit)
    validation = validate_chain()
    summary = get_chain_summary()
    return LedgerResponse(
        valid=bool(validation.get("valid", False)),
        length=int(validation.get("length", len(blocks))),
        offchain_length=int(validation.get("offchain_length", 0)),
        backend=str(summary.get("backend", "hybrid-local")),
        blocks=[PredictionBlockItem(**block) for block in blocks],
    )


@app.get("/ledger/ui", response_class=HTMLResponse)
def ledger_ui() -> HTMLResponse:
    blocks = get_chain(limit=None)
    validation = validate_chain()
    html = render_ledger_page(blocks=blocks, validation=validation)
    return HTMLResponse(content=html)


@app.get("/ledger/validate", response_model=LedgerValidateResponse)
def ledger_validate() -> LedgerValidateResponse:
    validation = validate_chain()
    return LedgerValidateResponse(
        valid=bool(validation.get("valid", False)),
        length=int(validation.get("length", 0)),
        offchain_length=int(validation.get("offchain_length", 0)),
        broken_index=int(validation.get("broken_index", -1)),
        reason=str(validation.get("reason", "")),
    )


@app.get("/ledger/export.json")
def ledger_export_json() -> Response:
    payload = export_chain_json()
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.json"'},
    )


@app.get("/ledger/export.csv")
def ledger_export_csv() -> Response:
    payload = export_chain_csv()
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.csv"'},
    )
