import Link from "next/link";
import { notFound } from "next/navigation";
import RiskBadge from "@/components/RiskBadge";
import { HOME_LABEL, PURPOSE_LABEL, getApplication } from "@/lib/api";

export const dynamic = "force-dynamic";

// Sonuç sayfası (ilk sürüm): olasılık, risk grubu, girdi özeti. Gerekçeler İP 5'te SHAP ile eklenecek.
export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const detail = await getApplication(id);
  if (!detail) notFound();
  const { input, prediction } = detail;
  const pct = prediction ? (prediction.default_probability * 100).toFixed(1) : null;

  const rows: [string, string][] = [
    ["Kredi tutarı", `${input.loan_amnt.toLocaleString("tr-TR")} USD`],
    ["Amaç", PURPOSE_LABEL[input.purpose] ?? input.purpose],
    ["Yıllık gelir", `${input.annual_inc.toLocaleString("tr-TR")} USD`],
    ["Borç / gelir", `%${input.dti}`],
    ["Çalışma süresi", input.emp_length ?? "Bilinmiyor"],
    ["Ev sahipliği", HOME_LABEL[input.home_ownership] ?? input.home_ownership],
    ["FICO", `${input.fico_range_low}–${input.fico_range_high}`],
    ["En eski kredi hesabı", input.earliest_cr_line],
    ["Açık hesap", String(input.open_acc)],
    ["Gecikme (2 yıl)", String(input.delinq_2yrs)],
    ["Döner kullanım", input.revol_util == null ? "—" : `%${input.revol_util}`],
    ["Sorgu (6 ay)", String(input.inq_last_6mths)],
  ];

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-semibold">Başvuru #{detail.application_id}</h1>
        <span className="text-sm text-slate-500">{new Date(detail.created_at).toLocaleString("tr-TR")}</span>
      </div>

      {prediction ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border bg-white p-5 sm:col-span-2">
            <p className="text-sm text-slate-600">Risk grubu</p>
            <div className="mt-2"><RiskBadge group={prediction.risk_group} large /></div>
            <p className="mt-4 text-sm text-slate-600">Tahmini temerrüt olasılığı</p>
            <p className="text-4xl font-semibold">%{pct}</p>
            <p className="mt-2 text-xs text-slate-500">
              {prediction.calibrated
                ? "Kalibre edilmiş olasılık: benzer başvuruların 36 ay içinde batma oranı."
                : "Kalibre edilmemiş skor (temel çizgi model); gerçek oran olarak okunmamalıdır."}
              {" "}Model: {prediction.model_version}
            </p>
          </div>
          <div className="rounded-lg border bg-white p-5">
            <p className="text-sm font-medium">Gerekçeler</p>
            {prediction.reasons.length ? (
              <ul className="mt-2 list-disc pl-5 text-sm">{prediction.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
            ) : (
              <p className="mt-2 text-sm text-slate-500">Türkçe gerekçeler İP 5'te SHAP değerleriyle eklenecek.</p>
            )}
          </div>
        </div>
      ) : (
        <p className="rounded-md border bg-white p-4 text-sm">Bu başvuru için henüz tahmin yok.</p>
      )}

      <div className="rounded-lg border bg-white">
        <h2 className="border-b px-5 py-3 text-sm font-semibold">Girilen bilgiler</h2>
        <dl className="grid gap-x-6 gap-y-2 px-5 py-4 text-sm sm:grid-cols-2">
          {rows.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4 border-b border-slate-100 py-1">
              <dt className="text-slate-600">{k}</dt><dd className="font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="flex gap-4 text-sm">
        <Link href="/basvuru" className="rounded-md bg-slate-900 px-4 py-2 text-white">Yeni başvuru</Link>
        <Link href="/gecmis" className="rounded-md border px-4 py-2">Başvuru geçmişi</Link>
      </div>
    </section>
  );
}
