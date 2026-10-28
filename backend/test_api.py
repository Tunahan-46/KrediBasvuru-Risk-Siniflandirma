"""Duman testi: python backend/test_api.py  (geçici SQLite veritabanı kullanır)"""
import os, sys, tempfile, time
from pathlib import Path

tmp = Path(tempfile.mkdtemp()) / "test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402
from backend.app.main import app  # noqa: E402

SAMPLE = {
    "loan_amnt": 10000, "annual_inc": 49200, "dti": 20.0, "emp_length": "10+ years",
    "home_ownership": "RENT", "purpose": "other", "fico_range_low": 690, "fico_range_high": 694,
    "open_acc": 10, "delinq_2yrs": 0, "revol_util": 21.0, "inq_last_6mths": 1, "earliest_cr_line": "Feb-1996",
}
RISKY = {**SAMPLE, "loan_amnt": 30000, "annual_inc": 30000, "dti": 35.0, "purpose": "small_business",
         "fico_range_low": 665, "fico_range_high": 669, "inq_last_6mths": 4, "revol_util": 95.0, "emp_length": "< 1 year"}
SAFE = {**SAMPLE, "loan_amnt": 6000, "annual_inc": 120000, "dti": 5.0, "purpose": "credit_card",
        "fico_range_low": 790, "fico_range_high": 794, "inq_last_6mths": 0, "revol_util": 8.0, "home_ownership": "MORTGAGE"}

with TestClient(app) as client:
    h = client.get("/health"); print("GET /health ->", h.status_code, h.json())
    assert h.json()["model_loaded"] and h.json()["database_ok"]
    results = []
    for name, body in [("örnek", SAMPLE), ("riskli", RISKY), ("güvenli", SAFE)]:
        t0 = time.perf_counter(); r = client.post("/predict", json=body); dt = (time.perf_counter() - t0) * 1000
        assert r.status_code == 200, r.text
        j = r.json(); results.append(j)
        print(f"POST /predict ({name}) -> p={j['default_probability']:.4f} {j['risk_group']} ({dt:.1f} ms)")
    bad = client.post("/predict", json={**SAMPLE, "fico_range_low": 100}); print("Geçersiz girdi ->", bad.status_code)
    assert bad.status_code == 422
    lst = client.get("/applications?limit=10"); assert lst.status_code == 200 and len(lst.json()) == 3
    print("GET /applications ->", len(lst.json()), "kayıt; en yeni:", lst.json()[0]["application_id"])
    one = client.get(f"/applications/{results[1]['application_id']}"); assert one.status_code == 200
    assert one.json()["prediction"]["default_probability"] == results[1]["default_probability"]
    assert one.json()["input"]["purpose"] == "small_business"
    print("GET /applications/{id} ->", one.json()["prediction"]["risk_group"])
    assert client.get("/applications/999999").status_code == 404
    print("Duman testi geçti (veritabanı: %s)." % h.json()["database"])
