"""İstek / yanıt şemaları (Pydantic). Alanlar 2. hafta Bölüm 2.3'teki 12 bağımsız değişkendir."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

HomeOwnership = Literal["RENT", "MORTGAGE", "OWN", "OTHER", "NONE", "ANY"]


class LoanApplication(BaseModel):
    loan_amnt: float = Field(..., gt=0, description="Kredi tutarı (USD)")
    annual_inc: float = Field(..., ge=0, description="Yıllık gelir (USD)")
    dti: float = Field(..., ge=0, description="Borç/gelir oranı (%)")
    emp_length: str | None = Field(None, description="Çalışma süresi, ör. '< 1 year', '3 years', '10+ years'")
    home_ownership: HomeOwnership = Field(..., description="Ev sahipliği durumu")
    purpose: str = Field(..., description="Kredi amacı, ör. 'credit_card', 'debt_consolidation'")
    fico_range_low: float = Field(..., ge=300, le=850)
    fico_range_high: float = Field(..., ge=300, le=850)
    open_acc: float = Field(..., ge=0, description="Açık hesap sayısı")
    delinq_2yrs: float = Field(..., ge=0, description="Son 2 yıldaki gecikme sayısı")
    revol_util: float | None = Field(None, ge=0, description="Döner kredi kullanım oranı (%)")
    inq_last_6mths: float = Field(..., ge=0, description="Son 6 aydaki sorgu sayısı")
    earliest_cr_line: str = Field(..., description="En eski kredi hesabı, 'Jan-1985' biçiminde")
    issue_d: date | None = Field(None, description="Başvuru tarihi; boşsa bugün")


class Prediction(BaseModel):
    default_probability: float = Field(..., description="Temerrüt olasılığı (0–1); henüz kalibre edilmemiş")
    risk_group: Literal["Düşük", "Orta", "Yüksek"]
    model_version: str
    reasons: list[str] = Field(default_factory=list, description="Türkçe gerekçeler (İP 5'te SHAP ile doldurulacak)")


class Health(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None
