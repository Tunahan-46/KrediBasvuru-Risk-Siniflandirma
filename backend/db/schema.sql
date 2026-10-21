-- KrediLens PostgreSQL şeması (3. hafta taslağı; İP 5'te uygulanacak)
-- Başvuru girdileri ve model çıktıları ayrı tutulur; aynı başvuru farklı
-- model sürümleriyle yeniden puanlanabilir.

CREATE TABLE IF NOT EXISTS applications (
    id                BIGSERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    loan_amnt         NUMERIC(12,2) NOT NULL,
    annual_inc        NUMERIC(14,2) NOT NULL,
    dti               NUMERIC(6,2)  NOT NULL,
    emp_length        TEXT,
    home_ownership    TEXT NOT NULL,
    purpose           TEXT NOT NULL,
    fico_range_low    SMALLINT NOT NULL,
    fico_range_high   SMALLINT NOT NULL,
    open_acc          SMALLINT NOT NULL,
    delinq_2yrs       SMALLINT NOT NULL,
    revol_util        NUMERIC(6,2),
    inq_last_6mths    SMALLINT NOT NULL,
    earliest_cr_line  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id                  BIGSERIAL PRIMARY KEY,
    application_id      BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    scored_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_version       TEXT NOT NULL,
    default_probability NUMERIC(6,4) NOT NULL,
    risk_group          TEXT NOT NULL CHECK (risk_group IN ('Düşük', 'Orta', 'Yüksek')),
    reasons             JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_predictions_application ON predictions(application_id);
CREATE INDEX IF NOT EXISTS idx_applications_created ON applications(created_at DESC);
