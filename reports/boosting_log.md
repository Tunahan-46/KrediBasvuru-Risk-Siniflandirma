# Ana model günlüğü – XGBoost / LightGBM + Optuna (src/train_boosting.py)

Eğitim: 172,988 kayıt (2007–2013), doğrulama: 162,570 kayıt (2014). Test kümesi açılmadı.
Özellik sayısı: 30 (3. hafta ön işleme hattı). Hafif koşu: Optuna yok, sabit parametreler; ağaç sayısı doğrulama kümesinde erken durdurma (100 tur, en çok 1000) ile seçildi. 4 çekirdek, tohum 42.

## Ölçütler

| Model | ROC-AUC | Gini | KS | Brier |
|---|---|---|---|---|
| Lojistik regresyon (3. hafta) – eğitim | 0.6582 | 0.3165 | 0.2288 | 0.2318 |
| Lojistik regresyon (3. hafta) – doğrulama | 0.6507 | 0.3014 | 0.2194 | 0.2420 |
| XGBoost varsayılan – eğitim | 0.7647 | 0.5295 | 0.3782 | 0.0966 |
| XGBoost varsayılan – doğrulama | 0.6509 | 0.3019 | 0.2194 | 0.1147 |
| LightGBM varsayılan – eğitim | 0.7594 | 0.5187 | 0.3706 | 0.0975 |
| LightGBM varsayılan – doğrulama | 0.6522 | 0.3044 | 0.2216 | 0.1146 |
| XGBoost (sabit parametre, erken durdurma) – eğitim | 0.6942 | 0.3884 | 0.2777 | 0.1028 |
| XGBoost (sabit parametre, erken durdurma) – doğrulama | 0.6561 | 0.3122 | 0.2269 | 0.1142 |
| LightGBM (sabit parametre, erken durdurma) – eğitim | 0.6977 | 0.3954 | 0.2833 | 0.1027 |
| LightGBM (sabit parametre, erken durdurma) – doğrulama | 0.6560 | 0.3120 | 0.2267 | 0.1142 |

Seçilen ana model: **XGBoost (sabit parametre, erken durdurma)**.

## En iyi parametreler

- XGBoost (sabit parametre, erken durdurma): `{"learning_rate": 0.05, "max_depth": 5, "min_child_weight": 10.0, "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0, "reg_alpha": 0.0, "gamma": 0.0, "scale_pos_weight": 1.0, "n_estimators": 206}`
- LightGBM (sabit parametre, erken durdurma): `{"learning_rate": 0.05, "num_leaves": 31, "min_child_samples": 100, "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0, "reg_alpha": 0.0, "scale_pos_weight": 1.0, "n_estimators": 150}`

## Deneme sayısı ve süreler

- XGBoost varsayılan: 1.4 sn
- LightGBM varsayılan: 1.0 sn
- XGBoost (sabit parametre, erken durdurma) – erken durdurma: 6.0 sn
- XGBoost (sabit parametre, erken durdurma): 0.7 sn
- LightGBM (sabit parametre, erken durdurma) – erken durdurma: 2.4 sn
- LightGBM (sabit parametre, erken durdurma): 0.5 sn

## Özellik önemleri – XGBoost (sabit parametre, erken durdurma) (gain, toplamın payı)

| ozellik | pay |
|---|---|
| fico | 0.1366 |
| purpose_small_business | 0.0682 |
| inq_last_6mths | 0.0657 |
| annual_inc | 0.0633 |
| purpose_credit_card | 0.0602 |
| emp_length_missing | 0.0448 |
| purpose_other | 0.0429 |
| home_ownership_MORTGAGE | 0.0408 |
| home_ownership_RENT | 0.0360 |
| loan_to_income | 0.0345 |
| purpose_debt_consolidation | 0.0337 |
| purpose_medical | 0.0276 |
| dti | 0.0273 |
| purpose_moving | 0.0253 |
| revol_util | 0.0251 |
| emp_length_num | 0.0226 |
| loan_amnt | 0.0225 |
| purpose_major_purchase | 0.0210 |
| credit_age_months | 0.0206 |
| open_acc | 0.0202 |
| purpose_house | 0.0200 |
| purpose_vacation | 0.0179 |
| delinq_2yrs | 0.0178 |
| purpose_home_improvement | 0.0169 |
| purpose_wedding | 0.0158 |
| home_ownership_OWN | 0.0157 |
| purpose_educational | 0.0155 |
| purpose_infrequent_sklearn | 0.0151 |
| purpose_car | 0.0134 |
| home_ownership_infrequent_sklearn | 0.0131 |

Çıktılar: `models/main_model_uncalibrated.joblib`, `models/main_model_meta.json`, `reports/figures/roc_compare.png`, `reports/figures/importance_main.png`
