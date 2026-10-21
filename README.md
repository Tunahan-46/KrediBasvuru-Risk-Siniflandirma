# KrediLens – Kredi Başvurularının Risk Gruplarına Göre Sınıflandırılması

Fırat Üniversitesi Bilgisayar Mühendisliği Tasarım Dersi, Proje No 78.
Ekip: Dila ALPAY, Tunahan ÖZDİL, Furkan COŞKUN.

Sistem, bir kredi başvurusunu başvuru anındaki bilgilerle **Düşük / Orta / Yüksek**
risk grubuna atar ve kararın gerekçesini Türkçe gösterir. Veri: Lending Club (Kaggle).

## Klasör yapısı

```
data/raw/          Ham Kaggle dosyası (depoya girmez)
data/processed/    Süzülmüş ve bölünmüş Parquet dosyaları (depoya girmez)
data/              Sızıntı sütunu listesi, değişken sözlüğü
src/               Veri hazırlama, ön işleme hattı ve model betikleri
models/            Eğitilmiş model dosyaları (ön işleme + model, joblib)
backend/           FastAPI uygulaması, Pydantic şemaları, PostgreSQL şeması, duman testi
frontend/          Next.js ön yüz iskeleti
notebooks/         Keşifsel analiz defteri
reports/           EDA özeti, model günlükleri ve grafikler
```

## Kurulum (macOS, Apple Silicon)

```bash
# 1. uv (Python yöneticisi) – bir kez
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sanal ortam ve bağımlılıklar
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Veri hazırlama (İP 2)

1. Ham dosyayı `data/raw/` içine koyun. İki kaynaktan biri yeterlidir:
   - Kaggle (giriş gerekir, 650 MB sıkıştırılmış): https://www.kaggle.com/datasets/wordsforthewise/lending-club
     dosya `accepted_2007_to_2018Q4.csv.gz`
   - Hugging Face (giriş gerekmez, 1,68 GB, aynı dosyanın açılmış hâli):
     ```bash
     curl -L -o data/raw/accepted_2007_to_2018Q4.csv \
       https://huggingface.co/datasets/codesignal/lending-club-loan-accepted/resolve/main/accepted_2007_to_2018Q4.csv
     ```
2. Tüm adımları tek komutla çalıştırın:

```bash
./run_data_pipeline.sh
```

Bu komut sırasıyla:

| Adım | Betik | Çıktı |
|---|---|---|
| Süzme ve sızıntı ayıklama | `src/filter_data.py` | `data/processed/loans_filtered.parquet` |
| Zamana göre bölme | `src/split_time.py` | `train.parquet` (2007–2013), `valid.parquet` (2014), `test.parquet` (2015) |
| Keşifsel analiz | `src/eda_summary.py` | `reports/eda_summary.md`, `reports/figures/*.png` |

Test kümesi modelleme bitene kadar açılmaz.

## Veri hazırlama sonuçları (15 Ekim 2026)

| Küme | Kayıt | Batık oranı |
|---|---|---|
| Ham veri (2007–2018, tüm vadeler) | 2.260.668 | – |
| Süzülmüş çalışma kümesi (36 ay, 2007–2015, sonucu kesin) | 618.584 | %13,90 |
| Eğitim (2007–2013) | 172.988 | %12,43 |
| Doğrulama (2014) | 162.570 | %13,73 |
| Test (2015, kilitli) | 283.026 | %14,89 |

Ayrıntı: `reports/filter_log.md`, `reports/split_log.md`, `reports/eda_summary.md`, `reports/figures/`.

## Modelleme – 1. yarı (İP 3, 3. hafta)

```bash
./run_baseline.sh      # ön işleme hattı + lojistik regresyon + API duman testi
```

| Adım | Dosya | Çıktı |
|---|---|---|
| Ön işleme hattı (Pipeline) | `src/preprocess.py` | 12 ham değişken → 30 özellik; parametreler yalnızca eğitim kümesinden |
| Temel çizgi (lojistik regresyon) | `src/train_baseline.py` | `models/baseline_logreg.joblib`, `reports/baseline_log.md`, ROC/KS eğrileri |
| Arka uç iskeleti | `backend/app/main.py` | `GET /health`, `POST /predict`; `backend/db/schema.sql` |
| Ön yüz iskeleti | `frontend/` | Next.js yerleşimi, gezinme, ana sayfa, API istemcisi (`npm install` gerekir) |

Arka ucu çalıştırma: `.venv/bin/uvicorn backend.app.main:app --reload --port 8000`

### Temel çizgi sonuçları (21 Ekim 2026, doğrulama kümesi 2014; test açılmadı)

| Model / puan | ROC-AUC | KS | Brier |
|---|---|---|---|
| Lojistik regresyon – eğitim (2007–2013) | 0,658 | 0,229 | 0,232 |
| Lojistik regresyon – doğrulama (2014) | 0,651 | 0,219 | 0,242 |
| Kurum notu A–G – doğrulama (ön bilgi) | 0,650 | 0,237 | – |
| Kurum alt notu A1–G5 – doğrulama (ön bilgi) | 0,660 | 0,237 | – |

Olasılıklar sınıf ağırlığı nedeniyle henüz kalibre değildir; `/predict` eşikleri (0,35 / 0,55) geçicidir.

## Haftalık ilerleme

- Hafta 1: Proje planı, 7 iş paketi, H1–H8 hedefleri
- Hafta 2: İP 2 veri hazırlama
- Hafta 3: İP 3 ilk yarı – ön işleme hattı, lojistik regresyon temel çizgisi, FastAPI / Next.js iskeletleri
- Hafta 4 (plan): XGBoost / LightGBM, Optuna, kalibrasyon; PostgreSQL bağlantısı; başvuru formu sayfası
