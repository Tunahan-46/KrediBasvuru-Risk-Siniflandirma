"""
Adım 5 – Temel çizgi: lojistik regresyon (3. hafta, Hedef 3.2)

Ön işleme hattı + lojistik regresyonu EĞİTİM kümesinde eğitir, DOĞRULAMA
kümesinde ROC-AUC, KS ve Brier değerlerini hesaplar. Test kümesi AÇILMAZ.
Karşılaştırma için kurumun A–G notunun aynı doğrulama kümesindeki sıralama
gücü (ROC-AUC, KS) da hesaplanır; dönem sonu H4 sınaması test kümesinde
yapılacaktır, buradaki değer yalnızca ön bilgidir.

Üretilenler:
  models/baseline_logreg.joblib      Ön işleme + model (tek dosya)
  reports/baseline_log.md            Ölçütler, katsayılar
  reports/figures/roc_baseline.png   ROC eğrisi
  reports/figures/ks_baseline.png    KS eğrisi

Kullanım:
  python src/train_baseline.py --indir data/processed
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import RAW_COLUMNS, build_preprocessor  # noqa: E402

GRADE_ORDER = {g: i for i, g in enumerate("ABCDEFG", start=1)}


def ks_statistic(y_true: np.ndarray, score: np.ndarray) -> float:
    """İyi ve kötü müşterilerin puan dağılımları arasındaki en büyük fark."""
    fpr, tpr, _ = roc_curve(y_true, score)
    return float(np.max(tpr - fpr))


def evaluate(name: str, y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "Model": name,
        "ROC-AUC": roc_auc_score(y, p),
        "Gini": 2 * roc_auc_score(y, p) - 1,
        "KS": ks_statistic(y, p),
        "Brier": brier_score_loss(y, p) if np.all((p >= 0) & (p <= 1)) else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indir", default="data/processed")
    parser.add_argument("--model-out", default="models/baseline_logreg.joblib")
    parser.add_argument("--report", default="reports/baseline_log.md")
    parser.add_argument("--figdir", default="reports/figures")
    parser.add_argument("--C", type=float, default=1.0, help="Lojistik regresyon düzenlileştirme (ters) katsayısı")
    args = parser.parse_args()

    indir = Path(args.indir)
    train = pd.read_parquet(indir / "train.parquet")
    valid = pd.read_parquet(indir / "valid.parquet")
    # test.parquet bilinçli olarak OKUNMAZ.

    X_tr, y_tr = train[RAW_COLUMNS], train["target"].to_numpy()
    X_va, y_va = valid[RAW_COLUMNS], valid["target"].to_numpy()

    model = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", LogisticRegression(C=args.C, class_weight="balanced", max_iter=2000, solver="lbfgs")),
    ])
    t0 = time.time()
    model.fit(X_tr, y_tr)
    fit_sec = time.time() - t0

    p_tr = model.predict_proba(X_tr)[:, 1]
    p_va = model.predict_proba(X_va)[:, 1]

    rows = [
        evaluate("Lojistik regresyon – eğitim (2007–2013)", y_tr, p_tr),
        evaluate("Lojistik regresyon – doğrulama (2014)", y_va, p_va),
    ]

    # Kurum notu (A–G) ile ön karşılaştırma, yalnızca doğrulama kümesinde
    grade_path = indir / "lender_grade.parquet"
    grade_rows = []
    if grade_path.exists():
        g = pd.read_parquet(grade_path, columns=["id", "grade", "sub_grade"])
        gv = valid[["id", "target"]].merge(g, on="id", how="left")
        ok = gv["grade"].notna()
        score_grade = gv.loc[ok, "grade"].map(GRADE_ORDER).astype(float).to_numpy()
        sub_order = {s: i for i, s in enumerate(sorted(g["sub_grade"].dropna().unique()))}
        score_sub = gv.loc[ok, "sub_grade"].map(sub_order).astype(float).to_numpy()
        yg = gv.loc[ok, "target"].to_numpy()
        r1 = evaluate("Kurum notu A–G – doğrulama (2014)", yg, score_grade); r1["Brier"] = float("nan")
        r2 = evaluate("Kurum alt notu A1–G5 – doğrulama (2014)", yg, score_sub); r2["Brier"] = float("nan")
        grade_rows = [r1, r2]

    metrics = pd.DataFrame(rows + grade_rows)

    # Katsayılar
    feat_names = model.named_steps["prep"].get_feature_names_out()
    coef = pd.DataFrame({"ozellik": feat_names, "katsayi": model.named_steps["clf"].coef_[0]})
    coef["mutlak"] = coef["katsayi"].abs()
    coef = coef.sort_values("mutlak", ascending=False).drop(columns="mutlak")

    # Çizimler
    figdir = Path(args.figdir); figdir.mkdir(parents=True, exist_ok=True)
    fpr, tpr, thr = roc_curve(y_va, p_va)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, label=f"Lojistik regresyon (AUC={roc_auc_score(y_va, p_va):.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=0.8)
    plt.xlabel("Yanlış pozitif oranı"); plt.ylabel("Doğru pozitif oranı")
    plt.title("ROC eğrisi – doğrulama kümesi (2014)"); plt.legend(loc="lower right"); plt.tight_layout()
    plt.savefig(figdir / "roc_baseline.png", dpi=150); plt.close()

    ks_i = int(np.argmax(tpr - fpr))
    plt.figure(figsize=(6, 4))
    plt.plot(thr[1:], tpr[1:], label="Batık (kümülatif)")
    plt.plot(thr[1:], fpr[1:], label="Ödenen (kümülatif)")
    plt.vlines(thr[ks_i], fpr[ks_i], tpr[ks_i], colors="r", linestyles="--", label=f"KS={tpr[ks_i]-fpr[ks_i]:.3f}")
    plt.xlim(0, 1); plt.xlabel("Tahmin edilen olasılık eşiği"); plt.ylabel("Eşiğin üstünde kalan pay")
    plt.title("KS eğrisi – doğrulama kümesi (2014)"); plt.legend(); plt.tight_layout()
    plt.savefig(figdir / "ks_baseline.png", dpi=150); plt.close()

    # Model dosyası
    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)

    # Rapor
    def md(df: pd.DataFrame) -> str:
        cols = list(df.columns)
        out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for _, r in df.iterrows():
            out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r) + " |")
        return "\n".join(out)

    n_feat = len(feat_names)
    lines = [
        "# Temel çizgi günlüğü – lojistik regresyon (src/train_baseline.py)",
        "",
        f"Eğitim: {len(train):,} kayıt (2007–2013), doğrulama: {len(valid):,} kayıt (2014). Test kümesi açılmadı.",
        f"Ön işleme sonrası özellik sayısı: {n_feat}. class_weight='balanced', C={args.C}. Eğitim süresi: {fit_sec:.1f} sn.",
        "",
        "## Ölçütler",
        "",
        md(metrics),
        "",
        "Not: Brier puanı sınıf ağırlığı nedeniyle yüksektir; olasılıklar henüz kalibre edilmemiştir (İP 3 ikinci yarı).",
        "Kurum notu satırları yalnızca ön bilgidir; H4 sınaması dönem sonunda test kümesinde yapılacaktır.",
        "",
        "## Katsayılar (standartlaştırılmış özellikler, mutlak değere göre sıralı)",
        "",
        md(coef),
        "",
        f"Çıktılar: `{args.model_out}`, `{figdir}/roc_baseline.png`, `{figdir}/ks_baseline.png`",
    ]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
