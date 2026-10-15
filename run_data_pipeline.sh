#!/usr/bin/env bash
# İP 2 veri hazırlama adımlarını sırayla çalıştırır.
# Kullanım: ./run_data_pipeline.sh [ham_dosya]
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
RAW="${1:-data/raw/accepted_2007_to_2018Q4.csv.gz}"

echo "== 1/3 Süzme ve sızıntı ayıklama =="
$PY src/filter_data.py --input "$RAW" --outdir data/processed --report reports/filter_log.md
echo
echo "== 2/3 Zamana göre bölme =="
$PY src/split_time.py --indir data/processed --report reports/split_log.md
echo
echo "== 3/3 Keşifsel analiz =="
$PY src/eda_summary.py --indir data/processed --outdir reports
echo
echo "Tamamlandı. Özetler: reports/filter_log.md, reports/split_log.md, reports/eda_summary.md"
