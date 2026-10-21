#!/usr/bin/env bash
# 3. hafta: ön işleme hattı + lojistik regresyon temel çizgisi, ardından API duman testi.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
echo "== 1/2 Temel çizgi (lojistik regresyon) =="
$PY src/train_baseline.py --indir data/processed --report reports/baseline_log.md
echo
echo "== 2/2 API duman testi =="
$PY backend/test_api.py
