import Link from "next/link";

// Ana sayfa (H7'deki yedi sayfanın ilki). Diğer sayfalar İP 6'da eklenecek.
export default function HomePage() {
  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-semibold">Kredi başvurusu risk sınıflandırma</h1>
      <p className="max-w-2xl text-slate-600">
        KrediLens, bir kredi başvurusunu başvuru anındaki bilgilerle <strong>Düşük</strong>,{" "}
        <strong>Orta</strong> veya <strong>Yüksek</strong> risk grubuna atar ve kararın gerekçesini gösterir.
      </p>
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { title: "Veri", text: "Lending Club, 36 ay vade, 2007–2015, sızıntısız 618.584 kredi." },
          { title: "Model", text: "Lojistik regresyon temel çizgisi; XGBoost / LightGBM ana model (İP 3)." },
          { title: "Karşılaştırma", text: "Modelin risk grupları kurumun A–G notlarıyla kıyaslanır (H4)." },
        ].map((c) => (
          <div key={c.title} className="rounded-lg border bg-white p-4">
            <h2 className="font-medium">{c.title}</h2>
            <p className="mt-1 text-sm text-slate-600">{c.text}</p>
          </div>
        ))}
      </div>
      <Link href="/basvuru" className="inline-block rounded-md bg-slate-900 px-4 py-2 text-white">
        Yeni başvuru değerlendir
      </Link>
    </section>
  );
}
