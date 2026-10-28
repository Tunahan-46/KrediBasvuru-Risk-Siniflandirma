"""
Yan deneme – gecikme sayısının katsayısı (4. hafta; 3. hafta raporu Bölüm 4.3)

Üçüncü haftada delinq_2yrs (son 2 yıldaki gecikme sayısı) lojistik regresyonda
sıfıra yakın katsayı aldı. Bu betik (1) eğitim kümesinde gecikme sayısına göre
batık oranını, (2) FICO ile ilişkisini, (3) değişkenin ikili (var/yok) biçimde
kodlandığı lojistik regresyonun doğrulama ROC-AUC'sini ve katsayısını hesaplar.

Kullanım: python src/check_delinq.py --indir data/processed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import RAW_COLUMNS, build_preprocessor  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", default="data/processed")
    parser.add_argument("--report", default="reports/delinq_check.md")
    args = parser.parse_args()
    indir = Path(args.indir)
    train = pd.read_parquet(indir / "train.parquet")
    valid = pd.read_parquet(indir / "valid.parquet")

    d = train["delinq_2yrs"].fillna(0)
    bucket = pd.cut(d, bins=[-0.5, 0.5, 1.5, np.inf], labels=["0", "1", "2+"])
    fico = (train["fico_range_low"] + train["fico_range_high"]) / 2
    by = pd.DataFrame({"Gecikme": bucket, "target": train["target"], "fico": fico}).groupby("Gecikme", observed=True)
    tab = by.agg(Kayit=("target", "size"), Pay=("target", lambda s: len(s) / len(train)), Batik=("target", "mean"), FICO=("fico", "mean")).reset_index()

    def fit_eval(X_tr, X_va):
        m = Pipeline([("prep", build_preprocessor()), ("clf", LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000))])
        m.fit(X_tr, train["target"])
        names = list(m.named_steps["prep"].get_feature_names_out())
        coef = float(m.named_steps["clf"].coef_[0][names.index("delinq_2yrs")])
        return roc_auc_score(valid["target"], m.predict_proba(X_va)[:, 1]), coef

    auc0, c0 = fit_eval(train[RAW_COLUMNS], valid[RAW_COLUMNS])
    X_tr = train[RAW_COLUMNS].copy(); X_va = valid[RAW_COLUMNS].copy()
    X_tr["delinq_2yrs"] = (X_tr["delinq_2yrs"].fillna(0) > 0).astype(float)
    X_va["delinq_2yrs"] = (X_va["delinq_2yrs"].fillna(0) > 0).astype(float)
    auc1, c1 = fit_eval(X_tr, X_va)
    # FICO olmadan: gecikme tek başına bilgi taşıyor mu?
    cols = [c for c in RAW_COLUMNS if not c.startswith("fico")]
    X_tr2 = train[RAW_COLUMNS].copy(); X_tr2[["fico_range_low", "fico_range_high"]] = 700.0
    X_va2 = valid[RAW_COLUMNS].copy(); X_va2[["fico_range_low", "fico_range_high"]] = 700.0
    auc2, c2 = fit_eval(X_tr2, X_va2)

    lines = [
        "# Gecikme sayısı (delinq_2yrs) yan denemesi – src/check_delinq.py", "",
        "## Eğitim kümesinde gecikme sayısına göre batık oranı ve ortalama FICO", "",
        "| Gecikme | Kayıt | Pay | Batık oranı | Ort. FICO |", "|---|---|---|---|---|",
        *[f"| {r.Gecikme} | {r.Kayit:,} | {r.Pay:.1%} | {r.Batik:.1%} | {r.FICO:.0f} |" for r in tab.itertuples()],
        "", "## Lojistik regresyon varyantları (doğrulama 2014)", "",
        "| Varyant | ROC-AUC | delinq katsayısı |", "|---|---|---|",
        f"| Sayısal (3. hafta) | {auc0:.4f} | {c0:+.4f} |",
        f"| İkili (gecikme var/yok) | {auc1:.4f} | {c1:+.4f} |",
        f"| Sayısal, FICO sabitlenmiş (FICO=700) | {auc2:.4f} | {c2:+.4f} |",
    ]
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
