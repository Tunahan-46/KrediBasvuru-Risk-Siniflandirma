"""
KrediLens arka uç (4. hafta)

Uç noktalar:
  GET  /health                 Servis, model ve veritabanı durumu
  POST /predict                Tek başvuru: olasılık + risk grubu; başvuru ve tahmin veritabanına yazılır
  GET  /applications           Başvuru geçmişi (en yeni önce, ?limit=)
  GET  /applications/{id}      Tek başvuru ve son tahmini

Model: models/main_model.joblib (ön işleme + gradyan artırma + kalibrasyon, tek dosya)
ve models/model_card.json (sürüm, eşikler). Dosya yoksa 3. haftanın temel çizgisi
(models/baseline_logreg.joblib) geçici eşiklerle (0,35 / 0,55) kullanılır.

Çalıştırma:
  .venv/bin/uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import db
from .schemas import ApplicationDetail, ApplicationSummary, Health, LoanApplication, Prediction, Thresholds

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))  # joblib dosyaları src/preprocess.py ve src/calibration.py sınıflarına ihtiyaç duyar

MAIN_MODEL = ROOT / "models" / "main_model.joblib"
MODEL_CARD = ROOT / "models" / "model_card.json"
BASELINE = ROOT / "models" / "baseline_logreg.joblib"

state: dict = {"model": None, "version": None, "calibrated": False, "thresholds": (0.35, 0.55)}


def load_model() -> None:
    if MAIN_MODEL.exists() and MODEL_CARD.exists():
        card = json.loads(MODEL_CARD.read_text(encoding="utf-8"))
        state.update(model=joblib.load(MAIN_MODEL), version=card["model_version"], calibrated=True,
                     thresholds=(float(card["thresholds"]["low"]), float(card["thresholds"]["high"])))
    elif BASELINE.exists():
        state.update(model=joblib.load(BASELINE), version="baseline-logreg-2026w3", calibrated=False, thresholds=(0.35, 0.55))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    load_model()
    yield
    state["model"] = None


app = FastAPI(title="KrediLens API", version="0.2.0", lifespan=lifespan)


def risk_group(p: float) -> str:
    low, high = state["thresholds"]
    return "Düşük" if p < low else ("Orta" if p < high else "Yüksek")


def score(application: LoanApplication) -> float:
    model = state["model"]
    if model is None:
        raise HTTPException(status_code=503, detail="Model yüklü değil; önce src/train_boosting.py ve src/calibrate.py çalıştırın.")
    row = application.model_dump()
    row["issue_d"] = pd.Timestamp(row["issue_d"] or date.today())
    return float(model.predict_proba(pd.DataFrame([row]))[0, 1])


def to_prediction(pred: db.Prediction) -> Prediction:
    return Prediction(application_id=pred.application_id, prediction_id=pred.id, default_probability=float(pred.default_probability),
                      calibrated=pred.model_version == state["version"] and state["calibrated"],
                      risk_group=pred.risk_group, model_version=pred.model_version, reasons=list(pred.reasons or []))


@app.get("/health", response_model=Health)
def health(session: Session = Depends(db.get_session)) -> Health:
    try:
        session.execute(text("SELECT 1")); db_ok = True
    except Exception:
        db_ok = False
    loaded = state["model"] is not None
    low, high = state["thresholds"]
    return Health(status="ok", model_loaded=loaded, model_version=state["version"] if loaded else None, calibrated=state["calibrated"],
                  thresholds=Thresholds(low=low, high=high), database=db.dialect_name(), database_ok=db_ok)


@app.post("/predict", response_model=Prediction)
def predict(application: LoanApplication, session: Session = Depends(db.get_session)) -> Prediction:
    p = round(score(application), 4)
    record = db.Application(**application.model_dump(exclude={"issue_d"}))
    pred = db.Prediction(model_version=state["version"], default_probability=p, risk_group=risk_group(p), reasons=[])
    record.predictions.append(pred)
    session.add(record)
    session.commit()
    return to_prediction(pred)


@app.get("/applications", response_model=list[ApplicationSummary])
def list_applications(limit: int = Query(20, ge=1, le=200), session: Session = Depends(db.get_session)) -> list[ApplicationSummary]:
    apps = session.scalars(select(db.Application).order_by(db.Application.id.desc()).limit(limit)).all()
    out = []
    for a in apps:
        last = a.predictions[0] if a.predictions else None
        out.append(ApplicationSummary(
            application_id=a.id, created_at=a.created_at, loan_amnt=float(a.loan_amnt), purpose=a.purpose,
            fico=(a.fico_range_low + a.fico_range_high) / 2,
            default_probability=float(last.default_probability) if last else None,
            risk_group=last.risk_group if last else None, model_version=last.model_version if last else None))
    return out


@app.get("/applications/{application_id}", response_model=ApplicationDetail)
def get_application(application_id: int, session: Session = Depends(db.get_session)) -> ApplicationDetail:
    a = session.get(db.Application, application_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    fields = {k: getattr(a, k) for k in LoanApplication.model_fields if k != "issue_d"}
    for k in ("loan_amnt", "annual_inc", "dti", "revol_util"):
        if fields[k] is not None:
            fields[k] = float(fields[k])
    last = a.predictions[0] if a.predictions else None
    return ApplicationDetail(application_id=a.id, created_at=a.created_at, input=LoanApplication(**fields),
                             prediction=to_prediction(last) if last else None)
