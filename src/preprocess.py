"""
Adım 4 – Ön işleme hattı (3. hafta, Hedef 3.1)

2. hafta raporunun 2.3 bölümünde tanımlanan dönüşümleri scikit-learn
Pipeline olarak kodlar. Tüm parametreler (medyan, %99 kırpma sınırı,
ölçekleme, kategori listesi) yalnızca EĞİTİM kümesinden öğrenilir;
doğrulama ve test kümelerine aynı parametrelerle uygulanır.

Adımlar:
  1. FeatureBuilder   : ham sütunlardan türetilmiş özellikler
        emp_length        -> 0–10 sayı (+ eksik göstergesi)
        fico_range_*      -> iki sınırın ortalaması (fico)
        earliest_cr_line  -> issue_d ile farkı, ay (credit_age_months)
        loan_amnt/annual_inc -> tutar/gelir oranı (loan_to_income)
  2. ColumnTransformer
        sayısal   : medyan doldurma -> %99 kırpma (gelir) -> log1p (gelir) -> standartlaştırma
        kategorik : 'bilinmiyor' doldurma -> one-hot (nadir seviyeler birleştirilir)

Kullanım (başka betikten):
  from preprocess import build_preprocessor, FEATURE_COLUMNS
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

# Modele giren ham sütunlar (2. hafta, Bölüm 2.3)
RAW_COLUMNS = [
    "loan_amnt", "annual_inc", "dti", "emp_length", "home_ownership", "purpose",
    "fico_range_low", "fico_range_high", "open_acc", "delinq_2yrs", "revol_util",
    "inq_last_6mths", "earliest_cr_line", "issue_d",
]

NUMERIC_PLAIN = ["loan_amnt", "dti", "open_acc", "delinq_2yrs", "revol_util", "inq_last_6mths",
                 "emp_length_num", "emp_length_missing", "fico", "credit_age_months", "loan_to_income"]
NUMERIC_LOG_CLIP = ["annual_inc"]
CATEGORICAL = ["home_ownership", "purpose"]
FEATURE_COLUMNS = NUMERIC_PLAIN + NUMERIC_LOG_CLIP + CATEGORICAL


def parse_emp_length(series: pd.Series) -> pd.Series:
    """'< 1 year' -> 0, '10+ years' -> 10, '3 years' -> 3, eksik -> NaN."""
    s = series.astype("string").str.strip()
    s = s.str.replace("< 1 year", "0", regex=False).str.replace("10+ years", "10", regex=False)
    return pd.to_numeric(s.str.extract(r"(\d+)")[0], errors="coerce").astype(float)


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Ham sütunlardan türetilmiş özellikleri üretir; öğrenilen parametre yoktur."""

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        emp = parse_emp_length(X["emp_length"])
        X["emp_length_num"] = emp
        X["emp_length_missing"] = emp.isna().astype(float)
        X["fico"] = (X["fico_range_low"].astype(float) + X["fico_range_high"].astype(float)) / 2.0
        issue = pd.to_datetime(X["issue_d"], errors="coerce")
        earliest = pd.to_datetime(X["earliest_cr_line"].astype("string"), format="%b-%Y", errors="coerce")
        X["credit_age_months"] = ((issue.dt.year - earliest.dt.year) * 12 + (issue.dt.month - earliest.dt.month)).astype(float)
        X.loc[X["credit_age_months"] < 0, "credit_age_months"] = np.nan
        inc = X["annual_inc"].astype(float).where(X["annual_inc"].astype(float) > 0)
        X["loan_to_income"] = X["loan_amnt"].astype(float) / inc
        if "revol_util" in X and not pd.api.types.is_numeric_dtype(X["revol_util"]):
            X["revol_util"] = pd.to_numeric(X["revol_util"].astype("string").str.replace("%", "", regex=False), errors="coerce")
        return X[FEATURE_COLUMNS]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(FEATURE_COLUMNS, dtype=object)


class QuantileClipper(BaseEstimator, TransformerMixin):
    """Üst uç değerleri eğitim kümesinde öğrenilen yüzdelik sınırına kırpar."""

    def __init__(self, upper: float = 0.99):
        self.upper = upper

    def fit(self, X, y=None):
        self.upper_bounds_ = np.nanquantile(np.asarray(X, dtype=float), self.upper, axis=0)
        return self

    def transform(self, X):
        return np.minimum(np.asarray(X, dtype=float), self.upper_bounds_)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


def build_preprocessor() -> Pipeline:
    numeric_plain = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    numeric_log_clip = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clip", QuantileClipper(upper=0.99)),
        ("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="bilinmiyor")),
        ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=200, sparse_output=False)),
    ])
    columns = ColumnTransformer([
        ("num", numeric_plain, NUMERIC_PLAIN),
        ("inc", numeric_log_clip, NUMERIC_LOG_CLIP),
        ("cat", categorical, CATEGORICAL),
    ], verbose_feature_names_out=False)
    return Pipeline([("features", FeatureBuilder()), ("columns", columns)])
