# Gecikme sayısı (delinq_2yrs) yan denemesi – src/check_delinq.py

## Eğitim kümesinde gecikme sayısına göre batık oranı ve ortalama FICO

| Gecikme | Kayıt | Pay | Batık oranı | Ort. FICO |
|---|---|---|---|---|
| 0 | 147,563 | 85.3% | 12.4% | 705 |
| 1 | 17,972 | 10.4% | 12.5% | 688 |
| 2+ | 7,453 | 4.3% | 13.4% | 683 |

## Lojistik regresyon varyantları (doğrulama 2014)

| Varyant | ROC-AUC | delinq katsayısı |
|---|---|---|
| Sayısal (3. hafta) | 0.6507 | -0.0045 |
| İkili (gecikme var/yok) | 0.6505 | -0.0152 |
| Sayısal, FICO sabitlenmiş (FICO=700) | 0.6356 | +0.0574 |
