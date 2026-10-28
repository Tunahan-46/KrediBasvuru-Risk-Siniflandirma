# Kalibrasyon günlüğü (src/calibrate.py)

Model: XGBoost (sabit parametre, erken durdurma) (`models/main_model_uncalibrated.joblib`). Doğrulama 2014: A = Oca–Haz (71,955 kayıt, batık 13.22%) kalibratör uydurma; B = Tem–Ara (90,615 kayıt, batık 14.13%) ölçüm. Test kümesi açılmadı.

## B kümesinde ölçütler

| Olasılık | ROC-AUC | KS | Brier | Log-loss | ECE | Ort. tahmin | Gözlenen |
|---|---|---|---|---|---|---|---|
| Ham (kalibre edilmemiş) | 0.6577 | 0.2290 | 0.1168 | 0.3884 | 0.0103 | 0.1315 | 0.1413 |
| Platt (A'da uydurulmuş) | 0.6577 | 0.2290 | 0.1168 | 0.3882 | 0.0086 | 0.1339 | 0.1413 |
| İzotonik (A'da uydurulmuş) | 0.6574 | 0.2287 | 0.1168 | 0.3888 | 0.0083 | 0.1338 | 0.1413 |

Seçilen yöntem: **Platt** (B'de en düşük Brier). Dağıtım için 2014'ün tamamında yeniden uyduruldu → `models/main_model.joblib`.

## Geçici risk grubu eşikleri (kalibre PD): Düşük < 0.10 ≤ Orta < 0.20 ≤ Yüksek

| Grup | Pay | Gözlenen batık | Ort. kalibre PD |
|---|---|---|---|
| Düşük | 0.3399 | 0.0713 | 0.0698 |
| Orta | 0.5073 | 0.1531 | 0.1436 |
| Yüksek | 0.1528 | 0.2575 | 0.2442 |

Kalibre PD yüzdelikleri (B): %10: 0.059, %25: 0.086, %50: 0.125, %75: 0.173, %90: 0.221, %95: 0.251

Model kartı: `models/model_card.json` (sürüm xgb-fixed-platt-2026w4). Çizimler: `reports/figures/reliability.png`, `reports/figures/pd_hist.png`
