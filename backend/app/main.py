"""
KrediLens arka uç iskeleti (3. hafta, Hedef 3.3)

Uç noktalar:
  GET  /health   Servis ve model durumu
  POST /predict  Tek başvuru için temerrüt olasılığı ve geçici risk grubu

Model: models/baseline_logreg.joblib (ön işleme + lojistik regresyon, tek dosya).
Risk grubu eşikleri GEÇİCİDİR (0,35 / 0,55, sınıf ağırlıklı olasılık üzerinden);
kalıcı eşikler İP 4'te doğrulama kümesinde net kâra göre belirlenecektir.
PostgreSQL kaydı bu haftada yoktur; şema backend/db/schema.sql dosyasındadır.

Çalıştırma:
  .venv/bin/uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from .schemas import Health, LoanApplication, Prediction

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))  # joblib dosyası src/preprocess.py sınıflarına ihtiyaç duyar

MODEL_PATH = ROOT / "models" / "baseline_logreg.joblib"
MODEL_VERSION = "baseline-logreg-2026w3"
THRESHOLDS = (0.35, 0.55)  # geçici

state: dict = {"model": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_PATH.exists():
        state["model"] = joblib.load(MODEL_PATH)
    yield
    state["model"] = None


app = FastAPI(title="KrediLens API", version="0.1.0", lifespan=lifespan)


def risk_group(p: float) -> str:
    low, high = THRESHOLDS
    return "Düşük" if p < low else ("Orta" if p < high else "Yüksek")


@app.get("/health", response_model=Health)
def health() -> Health:
    loaded = state["model"] is not None
    return Health(status="ok", model_loaded=loaded, model_version=MODEL_VERSION if loaded else None)


@app.post("/predict", response_model=Prediction)
def predict(application: LoanApplication) -> Prediction:
    model = state["model"]
    if model is None:
        raise HTTPException(status_code=503, detail="Model yüklü değil; önce src/train_baseline.py çalıştırın.")
    row = application.model_dump()
    row["issue_d"] = pd.Timestamp(row["issue_d"] or date.today())
    frame = pd.DataFrame([row])
    p = float(model.predict_proba(frame)[0, 1])
    return Prediction(default_probability=round(p, 4), risk_group=risk_group(p), model_version=MODEL_VERSION)
