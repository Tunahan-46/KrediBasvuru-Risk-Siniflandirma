"""
Adım 2 – Zamana göre bölme (Hedef 2.4)

Süzülmüş veriyi kredinin verilme yılına göre üç kümeye ayırır:
  - Eğitim    : 2007–2013   -> ön işleme parametreleri yalnızca buradan öğrenilir
  - Doğrulama : 2014        -> hiperparametre ve eşik seçimi
  - Test      : 2015        -> KİLİTLİ; dönem sonunda bir kez açılır

Rastgele bölme yerine zamana göre bölme kullanılır; model gelecekteki
başvurularda kullanılacağından eğitildiği dönemden sonraki bir dönemde
sınanmalıdır (Lessmann vd., 2015).

Kullanım:
  python src/split_time.py --indir data/processed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TRAIN_YEARS = range(2007, 2014)  # 2007–2013
VALID_YEAR = 2014
TEST_YEAR = 2015


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indir", default="data/processed", help="loans_filtered.parquet'in bulunduğu klasör")
    parser.add_argument("--report", default="reports/split_log.md")
    args = parser.parse_args()

    indir = Path(indir_str := args.indir)
    src = indir / "loans_filtered.parquet"
    if not src.exists():
        raise SystemExit(f"Bulunamadı: {src}. Önce src/filter_data.py çalıştırın.")

    df = pd.read_parquet(src)

    train = df[df["issue_year"].isin(TRAIN_YEARS)]
    valid = df[df["issue_year"] == VALID_YEAR]
    test = df[df["issue_year"] == TEST_YEAR]

    assert len(train) + len(valid) + len(test) == len(df), "Kümeler toplamı tüm veriye eşit olmalı"

    train.to_parquet(indir / "train.parquet", index=False)
    valid.to_parquet(indir / "valid.parquet", index=False)
    test.to_parquet(indir / "test.parquet", index=False)

    def row(name: str, part: pd.DataFrame, note: str) -> str:
        rate = part["target"].mean() * 100 if len(part) else float("nan")
        return f"| {name} | {len(part):,} | {rate:.2f} % | {note} |"

    lines = [
        "# Zamana göre bölme günlüğü (src/split_time.py)",
        "",
        "| Küme | Kayıt | Batık oranı | Not |",
        "|---|---|---|---|",
        row("Eğitim (2007–2013)", train, "Ön işleme parametreleri buradan öğrenilir"),
        row("Doğrulama (2014)", valid, "Hiperparametre ve eşik seçimi"),
        row("Test (2015)", test, "Kilitli; dönem sonunda bir kez açılacak"),
        row("Toplam", df, ""),
        "",
        f"Çıktılar: `{indir_str}/train.parquet`, `valid.parquet`, `test.parquet`",
        "",
        "Not: test.parquet modelleme bitene kadar hiçbir betik veya defter tarafından okunmaz.",
    ]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
