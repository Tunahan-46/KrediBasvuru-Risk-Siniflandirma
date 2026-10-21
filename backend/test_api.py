"""Hızlı duman testi: python backend/test_api.py"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402
from backend.app.main import app  # noqa: E402

SAMPLE = {
    "loan_amnt": 10000, "annual_inc": 49200, "dti": 20.0, "emp_length": "10+ years",
    "home_ownership": "RENT", "purpose": "other", "fico_range_low": 690, "fico_range_high": 694,
    "open_acc": 10, "delinq_2yrs": 0, "revol_util": 21.0, "inq_last_6mths": 1, "earliest_cr_line": "Feb-1996",
}

with TestClient(app) as client:
    h = client.get("/health"); print("GET /health ->", h.status_code, h.json())
    t0 = time.perf_counter(); r = client.post("/predict", json=SAMPLE); dt = (time.perf_counter() - t0) * 1000
    print(f"POST /predict -> {r.status_code} {r.json()}  ({dt:.1f} ms)")
    bad = client.post("/predict", json={**SAMPLE, "fico_range_low": 100}); print("Geçersiz girdi ->", bad.status_code)
    assert h.json()["model_loaded"] and r.status_code == 200 and bad.status_code == 422
    print("Duman testi geçti.")
