# Temel çizgi günlüğü – lojistik regresyon (src/train_baseline.py)

Eğitim: 172,988 kayıt (2007–2013), doğrulama: 162,570 kayıt (2014). Test kümesi açılmadı.
Ön işleme sonrası özellik sayısı: 30. class_weight='balanced', C=1.0. Eğitim süresi: 1.0 sn.

## Ölçütler

| Model | ROC-AUC | Gini | KS | Brier |
|---|---|---|---|---|
| Lojistik regresyon – eğitim (2007–2013) | 0.6582 | 0.3165 | 0.2288 | 0.2318 |
| Lojistik regresyon – doğrulama (2014) | 0.6507 | 0.3014 | 0.2194 | 0.2420 |
| Kurum notu A–G – doğrulama (2014) | 0.6502 | 0.3003 | 0.2365 | nan |
| Kurum alt notu A1–G5 – doğrulama (2014) | 0.6596 | 0.3191 | 0.2365 | nan |

Not: Brier puanı sınıf ağırlığı nedeniyle yüksektir; olasılıklar henüz kalibre edilmemiştir (İP 3 ikinci yarı).
Kurum notu satırları yalnızca ön bilgidir; H4 sınaması dönem sonunda test kümesinde yapılacaktır.

## Katsayılar (standartlaştırılmış özellikler, mutlak değere göre sıralı)

| ozellik | katsayi |
|---|---|
| purpose_small_business | 0.7456 |
| purpose_credit_card | -0.4776 |
| fico | -0.3619 |
| purpose_infrequent_sklearn | 0.3411 |
| home_ownership_infrequent_sklearn | 0.3133 |
| purpose_major_purchase | -0.2912 |
| purpose_car | -0.2676 |
| purpose_debt_consolidation | -0.2576 |
| purpose_wedding | -0.2443 |
| annual_inc | -0.2365 |
| purpose_educational | 0.2055 |
| inq_last_6mths | 0.1945 |
| purpose_medical | 0.1785 |
| home_ownership_MORTGAGE | -0.1400 |
| purpose_vacation | 0.1325 |
| purpose_other | 0.1233 |
| loan_to_income | 0.1116 |
| purpose_moving | 0.1010 |
| purpose_home_improvement | -0.0908 |
| dti | 0.0832 |
| home_ownership_OWN | -0.0767 |
| revol_util | 0.0750 |
| emp_length_missing | 0.0660 |
| loan_amnt | 0.0587 |
| home_ownership_RENT | 0.0584 |
| purpose_house | -0.0433 |
| open_acc | 0.0403 |
| credit_age_months | -0.0326 |
| emp_length_num | 0.0249 |
| delinq_2yrs | -0.0045 |

Çıktılar: `models/baseline_logreg.joblib`, `reports/figures/roc_baseline.png`, `reports/figures/ks_baseline.png`
