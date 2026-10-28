"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { EMP_LENGTHS, HOME_OWNERSHIP, PURPOSES, monthToLcFormat, predict, type HomeOwnership } from "@/lib/api";

// Yeni başvuru formu (H7'deki ikinci sayfa). 12 model girdisi; FICO tek puan olarak alınır,
// Lending Club'daki 4 puanlık aralığa (alt = puan, üst = puan + 4) çevrilir.
type Form = {
  loan_amnt: string; annual_inc: string; dti: string; emp_length: string; home_ownership: HomeOwnership; purpose: string;
  fico: string; open_acc: string; delinq_2yrs: string; revol_util: string; inq_last_6mths: string; earliest_cr_line: string;
};

const initial: Form = {
  loan_amnt: "10000", annual_inc: "50000", dti: "18", emp_length: "5 years", home_ownership: "RENT", purpose: "debt_consolidation",
  fico: "690", open_acc: "9", delinq_2yrs: "0", revol_util: "45", inq_last_6mths: "1", earliest_cr_line: "2005-06",
};

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  );
}

const inputCls = "mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-500 focus:outline-none";

export default function ApplicationPage() {
  const router = useRouter();
  const [form, setForm] = useState<Form>(initial);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const fico = Number(form.fico);
    if (fico < 300 || fico > 846) return setError("FICO puanı 300–846 aralığında olmalıdır.");
    if (!form.earliest_cr_line) return setError("En eski kredi hesabı tarihi gerekli.");
    setBusy(true);
    try {
      const result = await predict({
        loan_amnt: Number(form.loan_amnt), annual_inc: Number(form.annual_inc), dti: Number(form.dti),
        emp_length: form.emp_length || null, home_ownership: form.home_ownership, purpose: form.purpose,
        fico_range_low: fico, fico_range_high: fico + 4, open_acc: Number(form.open_acc), delinq_2yrs: Number(form.delinq_2yrs),
        revol_util: form.revol_util === "" ? null : Number(form.revol_util), inq_last_6mths: Number(form.inq_last_6mths),
        earliest_cr_line: monthToLcFormat(form.earliest_cr_line),
      });
      router.push(`/sonuc/${result.application_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bilinmeyen hata");
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Yeni başvuru</h1>
        <p className="mt-1 text-sm text-slate-600">
          Başvuru anında bilinen 12 bilgi girilir; sistem temerrüt olasılığını ve risk grubunu hesaplar, başvuruyu kayıt altına alır.
        </p>
      </div>
      <form onSubmit={onSubmit} className="space-y-6 rounded-lg border bg-white p-6">
        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="mb-2 text-sm font-semibold text-slate-800">Kredi</legend>
          <Field label="Kredi tutarı (USD)"><input className={inputCls} type="number" min={500} step={100} required value={form.loan_amnt} onChange={set("loan_amnt")} /></Field>
          <Field label="Kredi amacı">
            <select className={inputCls} value={form.purpose} onChange={set("purpose")}>
              {PURPOSES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </Field>
        </fieldset>
        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="mb-2 text-sm font-semibold text-slate-800">Başvuran</legend>
          <Field label="Yıllık gelir (USD)"><input className={inputCls} type="number" min={0} step={1000} required value={form.annual_inc} onChange={set("annual_inc")} /></Field>
          <Field label="Borç / gelir oranı (%)" hint="Aylık borç ödemelerinin aylık gelire oranı"><input className={inputCls} type="number" min={0} max={100} step={0.1} required value={form.dti} onChange={set("dti")} /></Field>
          <Field label="Çalışma süresi">
            <select className={inputCls} value={form.emp_length} onChange={set("emp_length")}>
              <option value="">Bilinmiyor</option>
              {EMP_LENGTHS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </Field>
          <Field label="Ev sahipliği">
            <select className={inputCls} value={form.home_ownership} onChange={set("home_ownership")}>
              {HOME_OWNERSHIP.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </Field>
        </fieldset>
        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="mb-2 text-sm font-semibold text-slate-800">Kredi geçmişi</legend>
          <Field label="FICO puanı" hint="300–846"><input className={inputCls} type="number" min={300} max={846} required value={form.fico} onChange={set("fico")} /></Field>
          <Field label="En eski kredi hesabı (ay/yıl)"><input className={inputCls} type="month" required value={form.earliest_cr_line} onChange={set("earliest_cr_line")} /></Field>
          <Field label="Açık hesap sayısı"><input className={inputCls} type="number" min={0} required value={form.open_acc} onChange={set("open_acc")} /></Field>
          <Field label="Son 2 yıldaki gecikme sayısı"><input className={inputCls} type="number" min={0} required value={form.delinq_2yrs} onChange={set("delinq_2yrs")} /></Field>
          <Field label="Döner kredi kullanımı (%)" hint="Boş bırakılabilir"><input className={inputCls} type="number" min={0} max={200} step={0.1} value={form.revol_util} onChange={set("revol_util")} /></Field>
          <Field label="Son 6 aydaki kredi sorgusu"><input className={inputCls} type="number" min={0} required value={form.inq_last_6mths} onChange={set("inq_last_6mths")} /></Field>
        </fieldset>
        {error && <p className="rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}
        <div className="flex items-center gap-3">
          <button type="submit" disabled={busy} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">
            {busy ? "Değerlendiriliyor…" : "Değerlendir"}
          </button>
          <button type="button" onClick={() => setForm(initial)} className="text-sm text-slate-600 hover:text-slate-900">Sıfırla</button>
        </div>
      </form>
    </section>
  );
}
