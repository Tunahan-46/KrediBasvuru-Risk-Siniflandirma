// FastAPI istemcisi. Alan adları backend/app/schemas.py ile birebir aynıdır.

export type LoanApplication = {
  loan_amnt: number;
  annual_inc: number;
  dti: number;
  emp_length?: string | null;
  home_ownership: "RENT" | "MORTGAGE" | "OWN" | "OTHER" | "NONE" | "ANY";
  purpose: string;
  fico_range_low: number;
  fico_range_high: number;
  open_acc: number;
  delinq_2yrs: number;
  revol_util?: number | null;
  inq_last_6mths: number;
  earliest_cr_line: string;
};

export type Prediction = {
  default_probability: number;
  risk_group: "Düşük" | "Orta" | "Yüksek";
  model_version: string;
  reasons: string[];
};

export async function getHealth() {
  const r = await fetch("/api/health", { cache: "no-store" });
  if (!r.ok) throw new Error("Servis yanıt vermiyor");
  return r.json() as Promise<{ status: string; model_loaded: boolean; model_version: string | null }>;
}

export async function predict(body: LoanApplication): Promise<Prediction> {
  const r = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`Tahmin alınamadı (${r.status})`);
  return r.json();
}
