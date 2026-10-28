# KrediLens ön yüz (Next.js 16, Tailwind 4)

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000 ; /api/* istekleri FastAPI'ye (8000) yönlenir
```

Sayfalar (4. hafta): ana sayfa `/`, yeni başvuru formu `/basvuru` (POST /predict),
sonuç `/sonuc/[id]` (GET /applications/{id}), başvuru geçmişi `/gecmis` (GET /applications).
Senaryo simülatörü, portföy paneli ve model karşılaştırma sayfaları İP 6'da eklenecek.
Sunucu bileşenleri arka uca `API_URL` (varsayılan http://localhost:8000) ile ulaşır.
