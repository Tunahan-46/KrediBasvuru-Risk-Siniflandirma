"""İstek / yanıt şemaları (Pydantic). Girdi alanları 2. hafta Bölüm 2.3'teki 12 bağımsız değişkendir."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

HomeOwnership = Literal["RENT", "MORTGAGE", "OWN", "OTHER", "NONE", "ANY"]
RiskGroup = Literal["Düşük", "Orta", "Yüksek"]


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
    earliest_cr_line: str = Field(..., pattern=r"^[A-Z][a-z]{2}-\d{4}$", description="En eski kredi hesabı, 'Jan-1985' biçiminde")
    issue_d: date | None = Field(None, description="Başvuru tarihi; boşsa bugün")


class Prediction(BaseModel):
    application_id: int
    prediction_id: int
    default_probability: float = Field(..., description="Temerrüt olasılığı (0–1)")
    calibrated: bool = Field(..., description="Olasılık kalibre edilmiş mi (ana model) yoksa sınıf ağırlıklı ham skor mu (temel çizgi)")
    risk_group: RiskGroup
    model_version: str
    reasons: list[str] = Field(default_factory=list, description="Türkçe gerekçeler (İP 5'te SHAP ile doldurulacak)")


class ApplicationSummary(BaseModel):
    """Başvuru geçmişi listesi için tek satır."""
    application_id: int
    created_at: datetime
    loan_amnt: float
    purpose: str
    fico: float
    default_probability: float | None
    risk_group: RiskGroup | None
    model_version: str | None


class ApplicationDetail(BaseModel):
    application_id: int
    created_at: datetime
    input: LoanApplication
    prediction: Prediction | None


class Thresholds(BaseModel):
    low: float = Field(..., description="Bu değerin altı Düşük")
    high: float = Field(..., description="Bu değer ve üstü Yüksek")


class Health(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None
    calibrated: bool
    thresholds: Thresholds
    database: str
    database_ok: bool
