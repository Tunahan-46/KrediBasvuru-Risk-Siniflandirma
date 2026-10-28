"""
Adım 7 – Kalibrasyon ve geçici risk grubu eşikleri (4. hafta, Hedef 4.2)

Ana modelin (kalibre edilmemiş) olasılıkları DOĞRULAMA kümesinde kalibre edilir.
Dürüst bir ölçüm için 2014 yılı zamana göre ikiye bölünür:
  A = Ocak–Haziran 2014 : kalibratör burada uydurulur
  B = Temmuz–Aralık 2014: Brier, ECE ve güvenilirlik eğrisi burada ölçülür
Platt ve izotonik yöntemleri karşılaştırılır; B'de Brier'i düşük olan seçilir ve
dağıtım için 2014'ün tamamında yeniden uydurulur. Test kümesi AÇILMAZ.

Geçici eşikler (--low, --high) kalibre olasılık üzerindedir; kalıcı eşikler İP 4'te
net kâra göre belirlenecektir. Her grup için B'deki pay ve gözlenen batık oranı yazılır.

Üretilenler:
  models/main_model.joblib             Ön işleme + model + kalibratör (CalibratedModel)
  models/model_card.json               Sürüm, eşikler, ölçütler
  reports/calibration_log.md
  reports/figures/reliability.png      Güvenilirlik eğrisi (ham / Platt / izotonik, B)
  reports/figures/pd_hist.png          Kalibre olasılık dağılımı ve eşikler (B)

Kullanım: python src/calibrate.py --low 0.10 --high 0.20
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibration import CalibratedModel, IsotonicCalibrator, PlattCalibrator  # noqa: E402
from preprocess import RAW_COLUMNS  # noqa: E402
from train_baseline import ks_statistic  # noqa: E402


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Beklenen kalibrasyon hatası: eşit sayıda gözlemli 10 kutuda |gözlenen − tahmin| ağırlıklı ortalaması."""
    q = pd.qcut(p, bins, labels=False, duplicates="drop")
    df = pd.DataFrame({"y": y, "p": p, "q": q}).groupby("q")
    return float((df.size() / len(y) * (df["y"].mean() - df["p"].mean()).abs()).sum())


def reliability(y: np.ndarray, p: np.ndarray, bins: int = 10) -> pd.DataFrame:
    q = pd.qcut(p, bins, labels=False, duplicates="drop")
    g = pd.DataFrame({"y": y, "p": p, "q": q}).groupby("q")
    return pd.DataFrame({"tahmin": g["p"].mean(), "gozlenen": g["y"].mean(), "n": g.size()})


def summarize(name: str, y: np.ndarray, p: np.ndarray) -> dict:
    return {"Olasılık": name, "ROC-AUC": roc_auc_score(y, p), "KS": ks_statistic(y, p), "Brier": brier_score_loss(y, p),
            "Log-loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), "ECE": ece(y, p), "Ort. tahmin": float(p.mean()), "Gözlenen": float(y.mean())}


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indir", default="data/processed")
    parser.add_argument("--model-in", default="models/main_model_uncalibrated.joblib")
    parser.add_argument("--meta-in", default="models/main_model_meta.json")
    parser.add_argument("--model-out", default="models/main_model.joblib")
    parser.add_argument("--card-out", default="models/model_card.json")
    parser.add_argument("--report", default="reports/calibration_log.md")
    parser.add_argument("--figdir", default="reports/figures")
    parser.add_argument("--low", type=float, default=0.10)
    parser.add_argument("--high", type=float, default=0.20)
    args = parser.parse_args()

    pipe = joblib.load(args.model_in)
    meta = json.loads(Path(args.meta_in).read_text(encoding="utf-8"))
    valid = pd.read_parquet(Path(args.indir) / "valid.parquet")
    # test.parquet bilinçli olarak OKUNMAZ.
    y = valid["target"].to_numpy()
    p_raw = pipe.predict_proba(valid[RAW_COLUMNS])[:, 1]
    month = pd.to_datetime(valid["issue_d"]).dt.month.to_numpy()
    A, B = month <= 6, month > 6
    print(f"A (Oca–Haz 2014): {A.sum():,} kayıt, batık {y[A].mean():.3%};  B (Tem–Ara 2014): {B.sum():,} kayıt, batık {y[B].mean():.3%}")

    cands = {"Platt": PlattCalibrator().fit(p_raw[A], y[A]), "İzotonik": IsotonicCalibrator().fit(p_raw[A], y[A])}
    rows = [summarize("Ham (kalibre edilmemiş)", y[B], p_raw[B])]
    pB = {}
    for name, cal in cands.items():
        pB[name] = cal.predict(p_raw[B])
        rows.append(summarize(name + " (A'da uydurulmuş)", y[B], pB[name]))
    table = pd.DataFrame(rows)
    best = min(cands, key=lambda k: brier_score_loss(y[B], pB[k]))
    print("Seçilen kalibrasyon:", best)

    # Dağıtım için 2014'ün tamamında yeniden uydur
    final_cal = (PlattCalibrator() if best == "Platt" else IsotonicCalibrator()).fit(p_raw, y)
    model = CalibratedModel(pipe, final_cal, best)
    p_cal_B = pB[best]

    # Eşikler ve risk grupları (B üzerinde)
    groups = np.where(p_cal_B < args.low, "Düşük", np.where(p_cal_B < args.high, "Orta", "Yüksek"))
    gdf = pd.DataFrame({"Grup": groups, "y": y[B], "p": p_cal_B}).groupby("Grup")
    gtab = pd.DataFrame({"Pay": gdf.size() / B.sum(), "Gözlenen batık": gdf["y"].mean(), "Ort. kalibre PD": gdf["p"].mean()}).reindex(["Düşük", "Orta", "Yüksek"]).reset_index()
    qs = np.quantile(p_cal_B, [0.1, 0.25, 0.5, 0.75, 0.9, 0.95])

    # Çizimler
    figdir = Path(args.figdir); figdir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.plot([0, 0.5], [0, 0.5], "k--", lw=0.8, label="Kusursuz kalibrasyon")
    for name, p in [("Ham", p_raw[B])] + list(pB.items()):
        r = reliability(y[B], p)
        plt.plot(r["tahmin"], r["gozlenen"], marker="o", ms=4, label=name)
    plt.xlabel("Ortalama tahmin edilen olasılık"); plt.ylabel("Gözlenen batık oranı")
    plt.title("Güvenilirlik eğrisi – Tem–Ara 2014"); plt.legend(fontsize=8); plt.tight_layout()
    plt.savefig(figdir / "reliability.png", dpi=150); plt.close()

    plt.figure(figsize=(6, 4))
    plt.hist(p_cal_B, bins=60, color="steelblue")
    for t, lab in [(args.low, f"Düşük | Orta ({args.low:.2f})"), (args.high, f"Orta | Yüksek ({args.high:.2f})")]:
        plt.axvline(t, color="r", ls="--", label=lab)
    plt.xlabel("Kalibre temerrüt olasılığı"); plt.ylabel("Başvuru sayısı"); plt.title("Kalibre olasılık dağılımı – Tem–Ara 2014")
    plt.legend(fontsize=8); plt.tight_layout(); plt.savefig(figdir / "pd_hist.png", dpi=150); plt.close()

    # Kaydet
    joblib.dump(model, args.model_out)
    short = ("lgbm" if "LightGBM" in meta["selected"] else "xgb") + ("-optuna" if meta.get("mode") == "optuna" else "-fixed")
    cal_short = "platt" if best == "Platt" else "isotonic"
    card = {
        "model_version": f"{short}-{cal_short}-2026w4",
        "selected": meta["selected"], "calibration": best, "calibration_fit_on": "2014 (tamamı); seçim A=Oca–Haz, ölçüm B=Tem–Ara",
        "thresholds": {"low": args.low, "high": args.high, "note": "Geçici; kalıcı eşikler İP 4'te net kâra göre"},
        "valid_metrics_B": {r["Olasılık"]: {k: float(v) for k, v in r.items() if k != "Olasılık"} for r in rows},
        "risk_groups_B": {r.Grup: {"pay": float(r.Pay), "gozlenen_batik": float(r._3), "ort_pd": float(r._4)} for r in gtab.itertuples()},
        "params": meta["params"], "n_features": meta["n_features"], "train": "2007–2013 (172.988)", "valid": "2014 (162.570)",
        "created": date.today().isoformat(),
    }
    Path(args.card_out).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Kalibrasyon günlüğü (src/calibrate.py)", "",
        f"Model: {meta['selected']} (`{args.model_in}`). Doğrulama 2014: A = Oca–Haz ({A.sum():,} kayıt, batık {y[A].mean():.2%}) kalibratör uydurma; "
        f"B = Tem–Ara ({B.sum():,} kayıt, batık {y[B].mean():.2%}) ölçüm. Test kümesi açılmadı.", "",
        "## B kümesinde ölçütler", "", md(table), "",
        f"Seçilen yöntem: **{best}** (B'de en düşük Brier). Dağıtım için 2014'ün tamamında yeniden uyduruldu → `{args.model_out}`.", "",
        f"## Geçici risk grubu eşikleri (kalibre PD): Düşük < {args.low:.2f} ≤ Orta < {args.high:.2f} ≤ Yüksek", "", md(gtab), "",
        "Kalibre PD yüzdelikleri (B): " + ", ".join(f"%{q*100:.0f}: {v:.3f}" for q, v in zip([0.1, 0.25, 0.5, 0.75, 0.9, 0.95], qs)), "",
        f"Model kartı: `{args.card_out}` (sürüm {card['model_version']}). Çizimler: `{figdir}/reliability.png`, `{figdir}/pd_hist.png`",
    ]
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
