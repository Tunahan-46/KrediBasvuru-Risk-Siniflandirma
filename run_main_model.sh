#!/usr/bin/env bash
# 4. hafta: XGBoost / LightGBM + Optuna, kalibrasyon ve geçici eşikler, ardından API duman testi.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
# Varsayılan hafif koşu: Optuna yok (TRIALS=0), 4 çekirdek, en çok 1.000 ağaç. Tam arama: TRIALS=40 NJOBS=8 MAXTREES=3000 ./run_main_model.sh
TRIALS="${TRIALS:-0}"; NJOBS="${NJOBS:-4}"; MAXTREES="${MAXTREES:-1000}"
echo "== 1/3 Ana model adayları (TRIALS=$TRIALS, $NJOBS çekirdek) =="
$PY src/train_boosting.py --indir data/processed --trials "$TRIALS" --n-jobs "$NJOBS" --max-trees "$MAXTREES" --report reports/boosting_log.md
echo
echo "== 2/3 Kalibrasyon ve geçici risk grubu eşikleri =="
$PY src/calibrate.py --indir data/processed --low "${LOW:-0.10}" --high "${HIGH:-0.20}"
echo
echo "== 3/3 API duman testi =="
$PY backend/test_api.py
