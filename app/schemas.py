from typing import List

from pydantic import BaseModel, Field


class PredictionItem(BaseModel):
    code: str
    label: str
    score: float
    diagnosis: str = ""
    overview: str = ""
    advice: List[str] = Field(default_factory=list)
    warning_signs: List[str] = Field(default_factory=list)


class PredictionResponse(BaseModel):
    model_dir: str
    top_k: int
    predictions: List[PredictionItem]


class PredictionBlockItem(BaseModel):
    index: int
    timestamp: str
    source: str
    image_name: str
    image_sha256: str
    model_dir: str
    top_k: int
    predictions: List[PredictionItem]
    record_id: str = ""
    offchain_record_id: str = ""
    payload_hash: str = ""
    storage: str = "off-chain-json"
    previous_hash: str
    hash: str
    signature: str
    writer_address: str = ""
    tx_hash: str = ""


class LedgerResponse(BaseModel):
    valid: bool
    length: int
    offchain_length: int = 0
    backend: str = "hybrid-local"
    blocks: List[PredictionBlockItem]


class LedgerValidateResponse(BaseModel):
    valid: bool
    length: int
    offchain_length: int = 0
    broken_index: int = -1
    reason: str = ""


class ScreenResponse(BaseModel):
    model_dir: str
    top_k: int
    predicted_code: str
    predicted_label: str
    diagnosis_summary: str = ""
    condition_overview: str = ""
    care_advice: List[str] = Field(default_factory=list)
    warning_signs: List[str] = Field(default_factory=list)
    medical_disclaimer: str = ""
    confidence: float
    red_flag_score: float
    priority: str
    risk_level: str
    risk_reason: str
    recommendation: str
    symptoms: dict
    predictions: List[PredictionItem]
