import Link from "next/link";
import RiskBadge from "@/components/RiskBadge";
import { PURPOSE_LABEL, listApplications } from "@/lib/api";

export const dynamic = "force-dynamic";

// Başvuru geçmişi (ilk sürüm): veritabanındaki son başvurular. Süzme ve sayfalama İP 6'da.
export default async function HistoryPage() {
  const items = await listApplications(50);
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Başvuru geçmişi</h1>
      {items.length === 0 ? (
        <p className="text-sm text-slate-600">Henüz kayıtlı başvuru yok. <Link href="/basvuru" className="underline">İlk başvuruyu değerlendirin.</Link></p>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left text-xs uppercase text-slate-600">
              <tr><th className="px-4 py-2">#</th><th className="px-4 py-2">Tarih</th><th className="px-4 py-2">Tutar</th><th className="px-4 py-2">Amaç</th><th className="px-4 py-2">FICO</th><th className="px-4 py-2">PD</th><th className="px-4 py-2">Grup</th></tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.application_id} className="border-t hover:bg-slate-50">
                  <td className="px-4 py-2"><Link href={`/sonuc/${a.application_id}`} className="underline">{a.application_id}</Link></td>
                  <td className="px-4 py-2">{new Date(a.created_at).toLocaleString("tr-TR")}</td>
                  <td className="px-4 py-2">{a.loan_amnt.toLocaleString("tr-TR")} USD</td>
                  <td className="px-4 py-2">{PURPOSE_LABEL[a.purpose] ?? a.purpose}</td>
                  <td className="px-4 py-2">{a.fico}</td>
                  <td className="px-4 py-2">{a.default_probability == null ? "—" : `%${(a.default_probability * 100).toFixed(1)}`}</td>
                  <td className="px-4 py-2">{a.risk_group ? <RiskBadge group={a.risk_group} /> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
