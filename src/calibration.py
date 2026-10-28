"""Kalibre edilmiş model sarmalayıcısı. joblib dosyası bu sınıfa ihtiyaç duyar (backend sys.path'e src ekler)."""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

EPS = 1e-6


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


class PlattCalibrator:
    """Platt ölçekleme: ham olasılığın logitine tek değişkenli lojistik regresyon."""

    def fit(self, p: np.ndarray, y: np.ndarray):
        self.lr_ = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(logit(p).reshape(-1, 1), y)
        return self

    def predict(self, p: np.ndarray) -> np.ndarray:
        return self.lr_.predict_proba(logit(p).reshape(-1, 1))[:, 1]


class IsotonicCalibrator:
    """İzotonik regresyon: ham olasılıktan gözlenen orana tekdüze artan basamaklı eşleme."""

    def fit(self, p: np.ndarray, y: np.ndarray):
        self.iso_ = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(p, y)
        return self

    def predict(self, p: np.ndarray) -> np.ndarray:
        return self.iso_.predict(p)


class CalibratedModel:
    """Ön işleme + sınıflandırıcı Pipeline'ının çıktısını kalibratörden geçirir; predict_proba arayüzü korunur."""

    def __init__(self, pipeline, calibrator, method: str):
        self.pipeline = pipeline
        self.calibrator = calibrator
        self.method = method

    def predict_raw(self, X) -> np.ndarray:
        return self.pipeline.predict_proba(X)[:, 1]

    def predict_proba(self, X) -> np.ndarray:
        p = self.calibrator.predict(self.predict_raw(X))
        return np.column_stack([1 - p, p])
