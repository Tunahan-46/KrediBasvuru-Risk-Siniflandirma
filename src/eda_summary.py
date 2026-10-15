"""
Adım 3 – Keşifsel analiz (Hedef 2.5)

Yalnızca eğitim ve doğrulama kümelerini kullanır; test kümesi AÇILMAZ.

Üretilenler:
  reports/eda_summary.md         Eksik değer oranları, sınıf dengesi, batık oranı kırılımları
  reports/figures/*.png          Çizimler

Kullanım:
  python src/eda_summary.py --indir data/processed --outdir reports
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

INT_COLUMNS = {"kayit", "count", "issue_year"}
NUMERIC = ["loan_amnt", "annual_inc", "dti", "fico_range_low", "open_acc", "delinq_2yrs", "revol_util", "inq_last_6mths"]


def to_number(series: pd.Series) -> pd.Series:
    """'%' işaretli metin sütunlarını sayıya çevirir (revol_util gibi)."""
    if series.dtype == object or str(series.dtype).startswith("str"):
        return pd.to_numeric(series.astype(str).str.replace("%", "", regex=False).str.strip(), errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def md_table(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    int_like = {c for c in cols if c in INT_COLUMNS or pd.api.types.is_integer_dtype(df[c])}
    for _, r in df.iterrows():
        cells = []
        for c, v in zip(cols, r):
            if c in int_like and pd.notna(v):
                cells.append(str(int(v)) if c == "issue_year" else f"{int(v):,}")
            elif isinstance(v, (float, np.floating)):
                cells.append(floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indir", default="data/processed")
    parser.add_argument("--outdir", default="reports")
    args = parser.parse_args()

    indir, outdir = Path(args.indir), Path(args.outdir)
    figdir = outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    train = pd.read_parquet(indir / "train.parquet")
    valid = pd.read_parquet(indir / "valid.parquet")
    df = pd.concat([train.assign(kume="egitim"), valid.assign(kume="dogrulama")], ignore_index=True)
    # test.parquet bilerek okunmaz

    df["revol_util"] = to_number(df["revol_util"])
    df["fico"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
    df["tutar_gelir"] = df["loan_amnt"] / df["annual_inc"].replace(0, pd.NA)

    sns.set_theme(style="whitegrid")
    sections: list[str] = ["# Keşifsel analiz özeti (eğitim + doğrulama; test kapalı)", ""]

    # 1. Sınıf dengesi
    cls = df.groupby("kume")["target"].agg(kayit="size", batik_orani=lambda s: s.mean() * 100).reset_index()
    sections += ["## 1. Sınıf dengesi", "", md_table(cls), "",
                 f"Toplam batık oranı: **{df['target'].mean() * 100:.2f} %**. Batık krediler azınlıkta; "
                 "eğitimde sınıf ağırlığı, değerlendirmede ROC-AUC ve KS kullanılacak.", ""]

    # 2. Eksik değerler
    miss = df.drop(columns=["kume"]).isna().mean().mul(100).sort_values(ascending=False)
    miss = miss[miss > 0].reset_index()
    miss.columns = ["sutun", "eksik_yuzde"]
    sections += ["## 2. Eksik değer oranları (%)", "", md_table(miss) if len(miss) else "Eksik değer yok.", "",
                 "Karar: sayısal eksikler eğitim kümesinin medyanıyla, kategorik eksikler 'bilinmiyor' seviyesiyle doldurulacak.", ""]

    # 3. Batık oranı: yıl
    by_year = df.groupby("issue_year")["target"].agg(kayit="size", batik_orani=lambda s: s.mean() * 100).reset_index()
    sections += ["## 3. Batık oranının yıla göre dağılımı", "", md_table(by_year), ""]
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=by_year, x="issue_year", y="batik_orani", ax=ax, color="#4C72B0")
    ax.set(xlabel="Verilme yılı", ylabel="Batık oranı (%)", title="Batık oranı – yıl")
    fig.tight_layout(); fig.savefig(figdir / "batik_orani_yil.png", dpi=130); plt.close(fig)

    # 4. Batık oranı: FICO aralığı
    bins = [600, 660, 680, 700, 720, 750, 850]
    df["fico_aralik"] = pd.cut(df["fico"], bins=bins, right=False)
    by_fico = df.groupby("fico_aralik", observed=True)["target"].agg(kayit="size", batik_orani=lambda s: s.mean() * 100).reset_index()
    by_fico["fico_aralik"] = by_fico["fico_aralik"].astype(str)
    sections += ["## 4. Batık oranının FICO aralığına göre dağılımı", "", md_table(by_fico), ""]
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=by_fico, x="fico_aralik", y="batik_orani", ax=ax, color="#DD8452")
    ax.set(xlabel="FICO aralığı", ylabel="Batık oranı (%)", title="Batık oranı – FICO")
    fig.tight_layout(); fig.savefig(figdir / "batik_orani_fico.png", dpi=130); plt.close(fig)

    # 5. Batık oranı: kredi amacı
    by_purpose = (df.groupby("purpose")["target"].agg(kayit="size", batik_orani=lambda s: s.mean() * 100)
                  .sort_values("batik_orani", ascending=False).reset_index())
    sections += ["## 5. Batık oranının kredi amacına göre dağılımı", "", md_table(by_purpose), ""]
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=by_purpose, y="purpose", x="batik_orani", ax=ax, color="#55A868")
    ax.set(ylabel="Kredi amacı", xlabel="Batık oranı (%)", title="Batık oranı – amaç")
    fig.tight_layout(); fig.savefig(figdir / "batik_orani_amac.png", dpi=130); plt.close(fig)

    # 6. Batık oranı: borç/gelir oranı
    df["dti_aralik"] = pd.cut(df["dti"], bins=[0, 10, 15, 20, 25, 30, 100], right=False)
    by_dti = df.groupby("dti_aralik", observed=True)["target"].agg(kayit="size", batik_orani=lambda s: s.mean() * 100).reset_index()
    by_dti["dti_aralik"] = by_dti["dti_aralik"].astype(str)
    sections += ["## 6. Batık oranının borç/gelir oranına göre dağılımı", "", md_table(by_dti), ""]

    # 7. Sayısal dağılımlar ve uç değerler
    desc = df[NUMERIC + ["tutar_gelir"]].describe(percentiles=[0.01, 0.5, 0.99]).T.reset_index()
    desc = desc.rename(columns={"index": "sutun"})[["sutun", "count", "mean", "1%", "50%", "99%", "max"]]
    sections += ["## 7. Sayısal değişkenlerin dağılımı", "", md_table(desc), "",
                 "Gözlem: annual_inc sütununda %99 ile max arasındaki fark büyükse logaritma ve %99 kırpma kararı geçerlidir.", ""]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, col in zip(axes.flat, ["loan_amnt", "annual_inc", "dti", "fico"]):
        sns.histplot(df[col].dropna().clip(upper=df[col].quantile(0.99)), bins=40, ax=ax, color="#8172B3")
        ax.set_title(f"{col} (%99'da kırpılmış)")
    fig.tight_layout(); fig.savefig(figdir / "dagilimlar.png", dpi=130); plt.close(fig)

    # 8. Metin biçimli sütunlar
    emp_vals = df["emp_length"].astype("string").fillna("<eksik>").value_counts().head(12).reset_index()
    emp_vals.columns = ["emp_length", "kayit"]
    sections += ["## 8. Metin biçimli sütun örneği: emp_length", "", md_table(emp_vals), "",
                 "Karar: '< 1 year' -> 0, '10+ years' -> 10, eksik -> ayrı seviye (bkz. data/variable_dictionary.csv).", ""]

    sections += ["## Üretilen çizimler", ""] + [f"- `figures/{p.name}`" for p in sorted(figdir.glob("*.png"))]

    out = outdir / "eda_summary.md"
    out.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print("\n".join(sections[:12]))
    print(f"\nYazıldı: {out}")
    print(f"Çizimler: {figdir}/")


if __name__ == "__main__":
    main()
