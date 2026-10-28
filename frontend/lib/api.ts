// FastAPI istemcisi. Alan adları backend/app/schemas.py ile birebir aynıdır.
// Tarayıcıda /api/* (next.config.ts yönlendirmesi), sunucu bileşenlerinde API_URL doğrudan kullanılır.

export type HomeOwnership = "RENT" | "MORTGAGE" | "OWN" | "OTHER" | "NONE" | "ANY";
export type RiskGroup = "Düşük" | "Orta" | "Yüksek";

export type LoanApplication = {
  loan_amnt: number;
  annual_inc: number;
  dti: number;
  emp_length?: string | null;
  home_ownership: HomeOwnership;
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
  application_id: number;
  prediction_id: number;
  default_probability: number;
  calibrated: boolean;
  risk_group: RiskGroup;
  model_version: string;
  reasons: string[];
};

export type ApplicationSummary = {
  application_id: number;
  created_at: string;
  loan_amnt: number;
  purpose: string;
  fico: number;
  default_probability: number | null;
  risk_group: RiskGroup | null;
  model_version: string | null;
};

export type ApplicationDetail = {
  application_id: number;
  created_at: string;
  input: LoanApplication;
  prediction: Prediction | null;
};

export const PURPOSES: { value: string; label: string }[] = [
  { value: "debt_consolidation", label: "Borç birleştirme" },
  { value: "credit_card", label: "Kredi kartı borcu" },
  { value: "home_improvement", label: "Ev tadilatı" },
  { value: "major_purchase", label: "Büyük alışveriş" },
  { value: "small_business", label: "Küçük işletme" },
  { value: "car", label: "Araç" },
  { value: "medical", label: "Sağlık" },
  { value: "moving", label: "Taşınma" },
  { value: "vacation", label: "Tatil" },
  { value: "house", label: "Konut" },
  { value: "wedding", label: "Düğün" },
  { value: "educational", label: "Eğitim" },
  { value: "renewable_energy", label: "Yenilenebilir enerji" },
  { value: "other", label: "Diğer" },
];

export const HOME_OWNERSHIP: { value: HomeOwnership; label: string }[] = [
  { value: "RENT", label: "Kiracı" },
  { value: "MORTGAGE", label: "Konut kredili ev sahibi" },
  { value: "OWN", label: "Ev sahibi" },
  { value: "OTHER", label: "Diğer" },
];

export const EMP_LENGTHS: { value: string; label: string }[] = [
  { value: "< 1 year", label: "1 yıldan az" },
  ...Array.from({ length: 9 }, (_, i) => ({ value: `${i + 1} year${i ? "s" : ""}`, label: `${i + 1} yıl` })),
  { value: "10+ years", label: "10 yıl ve üzeri" },
];

export const PURPOSE_LABEL = Object.fromEntries(PURPOSES.map((p) => [p.value, p.label]));
export const HOME_LABEL = Object.fromEntries(HOME_OWNERSHIP.map((p) => [p.value, p.label]));

const serverBase = () => process.env.API_URL ?? "http://localhost:8000";

/** "1996-02" (type=month) -> "Feb-1996" (Lending Club biçimi) */
export function monthToLcFormat(value: string): string {
  const [y, m] = value.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[m - 1]}-${y}`;
}

export async function predict(body: LoanApplication): Promise<Prediction> {
  const r = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let detail = "";
    try {
      const j = await r.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new Error(`Tahmin alınamadı (${r.status}) ${detail}`);
  }
  return r.json();
}

export async function getApplication(id: string): Promise<ApplicationDetail | null> {
  const r = await fetch(`${serverBase()}/applications/${id}`, { cache: "no-store" });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`Başvuru okunamadı (${r.status})`);
  return r.json();
}

export async function listApplications(limit = 20): Promise<ApplicationSummary[]> {
  const r = await fetch(`${serverBase()}/applications?limit=${limit}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`Geçmiş okunamadı (${r.status})`);
  return r.json();
}
