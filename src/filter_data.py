"""
Adım 1 – Süzme ve sızıntı ayıklama (Hedef 2.1 ve 2.2)

Ham Lending Club dosyasını parça parça ve yalnızca gerekli sütunlarla okur
(8 GB RAM'e sığması için), proje kapsamına uyan kredileri süzer ve
Parquet olarak kaydeder.

Süzme kuralları:
  - Vade: yalnızca 36 ay
  - Verilme tarihi: 2007–2015
  - Sonuç: yalnızca Fully Paid / Charged Off

Sızıntı sütunları hiç okunmaz (bkz. data/leakage_columns.md). Kurum notu
(grade, sub_grade, int_rate) modele verilmez; yalnızca dönem sonu
karşılaştırması (H4) için ayrı dosyada tutulur.

Kullanım:
  python src/filter_data.py \
      --input data/raw/accepted_2007_to_2018Q4.csv.gz \
      --outdir data/processed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Başvuru anında bilinen, modele girecek sütunlar (data/variable_dictionary.csv)
MODEL_COLUMNS = [
    "loan_amnt",
    "annual_inc",
    "dti",
    "emp_length",
    "home_ownership",
    "purpose",
    "fico_range_low",
    "fico_range_high",
    "open_acc",
    "delinq_2yrs",
    "revol_util",
    "inq_last_6mths",
    "earliest_cr_line",
]

# Süzme için gereken sütunlar
FILTER_COLUMNS = ["term", "issue_d", "loan_status"]

# Kurumun notu: modele verilmez, karşılaştırma için ayrı dosyada
LENDER_COLUMNS = ["grade", "sub_grade", "int_rate"]

ID_COLUMN = "id"

USECOLS = [ID_COLUMN] + FILTER_COLUMNS + MODEL_COLUMNS + LENDER_COLUMNS

KEEP_STATUS = {"Fully Paid", "Charged Off"}
YEAR_MIN, YEAR_MAX = 2007, 2015
CHUNKSIZE = 200_000


def filter_chunk(chunk: pd.DataFrame, counts: dict) -> pd.DataFrame:
    """Tek bir parçayı süzer ve sayaçları günceller."""
    counts["ham"] += len(chunk)

    # Dosya sonundaki özet satırları (id boş) ve loan_status boş kayıtlar
    chunk = chunk.dropna(subset=[ID_COLUMN, "loan_status", "issue_d", "term"])
    counts["gecerli_kayit"] += len(chunk)

    # Vade: ham veride " 36 months" biçiminde, baştaki boşluğa dikkat
    term = chunk["term"].astype(str).str.strip()
    chunk = chunk[term == "36 months"]
    counts["36_ay"] += len(chunk)

    # Verilme tarihi: "Dec-2015" biçimi
    issue_d = pd.to_datetime(chunk["issue_d"], format="%b-%Y", errors="coerce")
    chunk = chunk.assign(issue_d=issue_d, issue_year=issue_d.dt.year)
    chunk = chunk[(chunk["issue_year"] >= YEAR_MIN) & (chunk["issue_year"] <= YEAR_MAX)]
    counts["2007_2015"] += len(chunk)

    # Sonucu kesinleşmiş krediler
    chunk = chunk[chunk["loan_status"].isin(KEEP_STATUS)]
    counts["sonucu_kesin"] += len(chunk)

    return chunk


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default="data/raw/accepted_2007_to_2018Q4.csv.gz", help="Ham Kaggle dosyası (.csv veya .csv.gz)")
    parser.add_argument("--outdir", default="data/processed", help="Çıktı klasörü")
    parser.add_argument("--report", default="reports/filter_log.md", help="Süzme sayaçlarının yazılacağı dosya")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise SystemExit(
            f"Ham dosya bulunamadı: {input_path}\n"
            "Kaggle'dan accepted_2007_to_2018Q4.csv.gz dosyasını indirip data/raw/ içine koyun:\n"
            "https://www.kaggle.com/datasets/wordsforthewise/lending-club"
        )

    counts = {k: 0 for k in ["ham", "gecerli_kayit", "36_ay", "2007_2015", "sonucu_kesin"]}
    parts: list[pd.DataFrame] = []

    print(f"Okunuyor: {input_path}  (parça boyutu {CHUNKSIZE:,} satır, {len(USECOLS)} sütun)")
    reader = pd.read_csv(
        input_path,
        usecols=USECOLS,
        dtype={ID_COLUMN: "string"},
        chunksize=CHUNKSIZE,
        low_memory=False,
    )
    for i, chunk in enumerate(reader, start=1):
        parts.append(filter_chunk(chunk, counts))
        print(f"  parça {i:3d}: toplam okunan {counts['ham']:>10,}  süzülen {counts['sonucu_kesin']:>9,}", flush=True)

    df = pd.concat(parts, ignore_index=True)
    del parts

    # Hedef değişken: Fully Paid -> 0, Charged Off -> 1
    df["target"] = (df["loan_status"] == "Charged Off").astype("int8")

    # Model dosyası: id + model sütunları + tarih + hedef. Kurum notu YOK.
    model_df = df[[ID_COLUMN, "issue_d", "issue_year"] + MODEL_COLUMNS + ["target"]]
    model_path = outdir / "loans_filtered.parquet"
    model_df.to_parquet(model_path, index=False)

    # Kurum notu: yalnızca H4 karşılaştırması için, ayrı dosya
    lender_df = df[[ID_COLUMN, "issue_year"] + LENDER_COLUMNS + ["target"]]
    lender_path = outdir / "lender_grade.parquet"
    lender_df.to_parquet(lender_path, index=False)

    default_rate = df["target"].mean() * 100
    by_year = df.groupby("issue_year").size()

    lines = [
        "# Süzme günlüğü (src/filter_data.py)",
        "",
        f"Girdi: `{input_path}`",
        "",
        "| Adım | Kayıt sayısı |",
        "|---|---|",
        f"| Ham veri (tüm satırlar) | {counts['ham']:,} |",
        f"| Geçerli kayıt (özet satırları atıldı) | {counts['gecerli_kayit']:,} |",
        f"| 36 ay vadeli | {counts['36_ay']:,} |",
        f"| 2007–2015 arası verilmiş | {counts['2007_2015']:,} |",
        f"| Sonucu kesin (Fully Paid / Charged Off) | {counts['sonucu_kesin']:,} |",
        "",
        f"Batık oranı (çalışma kümesi): **{default_rate:.2f} %**",
        "",
        "## Yıla göre kayıt sayısı",
        "",
        "| Yıl | Kayıt |",
        "|---|---|",
    ] + [f"| {int(y)} | {n:,} |" for y, n in by_year.items()] + [
        "",
        f"Çıktılar: `{model_path}` (model sütunları), `{lender_path}` (kurum notu, modele verilmez)",
    ]
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print("\n".join(lines[4:12]))
    print(f"\nYazıldı: {model_path}  ({len(model_df):,} satır)")
    print(f"Yazıldı: {lender_path}")
    print(f"Günlük:  {args.report}")


if __name__ == "__main__":
    main()
