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
backend/           FastAPI uygulaması, Pydantic şemaları, SQLAlchemy ORM, PostgreSQL şeması, duman testi
frontend/          Next.js ön yüz (ana sayfa, başvuru formu, sonuç, geçmiş)
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

Temel çizginin olasılıkları sınıf ağırlığı nedeniyle kalibre değildir; 4. haftadan itibaren `/predict` kalibre ana modeli kullanır.

## Arka uç ve veritabanı (4. hafta)

```bash
.venv/bin/uvicorn backend.app.main:app --reload --port 8000     # varsayılan: SQLite (backend/db/dev.sqlite3)
docker compose up -d db                                           # PostgreSQL 16 (yaklaşık 100 MB imaj)
DATABASE_URL=postgresql+psycopg://kredilens:kredilens@localhost:5432/kredilens .venv/bin/uvicorn backend.app.main:app --port 8000
.venv/bin/python backend/test_api.py                              # duman testi (geçici SQLite ile)
.venv/bin/python backend/db/print_ddl.py                          # ORM'den PostgreSQL DDL; backend/db/schema.sql ile karşılaştırma
```

| Uç nokta | İşlev |
|---|---|
| `GET /health` | Servis, model sürümü, kalibrasyon durumu, eşikler, veritabanı bağlantısı |
| `POST /predict` | Olasılık + risk grubu; başvuru ve tahmin `applications` / `predictions` tablolarına yazılır |
| `GET /applications?limit=` | Başvuru geçmişi (en yeni önce) |
| `GET /applications/{id}` | Tek başvuru ve son tahmini |

Model yükleme sırası: `models/main_model.joblib` + `models/model_card.json` (kalibre ana model) varsa onlar; yoksa
`models/baseline_logreg.joblib` geçici eşiklerle (0,35 / 0,55, kalibre değil).

## Ön yüz (4. hafta)

```bash
cd frontend && npm install && npm run dev      # http://localhost:3000
```

Sayfalar: `/` ana sayfa, `/basvuru` yeni başvuru formu (POST /predict), `/sonuc/[id]` sonuç, `/gecmis` başvuru geçmişi.
Ayrıntı: `frontend/README.md`.

## Ana model, kalibrasyon ve eşikler (İP 3, 2. yarı, 4. hafta)

```bash
./run_main_model.sh                              # hafif koşu: Optuna yok, 4 çekirdek, en çok 1.000 ağaç (~1 dk)
TRIALS=10 NJOBS=4 ./run_main_model.sh            # Optuna araması (5. hafta planı)
```

| Adım | Betik | Çıktı |
|---|---|---|
| XGBoost / LightGBM (erken durdurma; `--trials N` ile Optuna) | `src/train_boosting.py` | `models/main_model_uncalibrated.joblib`, `reports/boosting_log.md`, ROC / önem grafikleri |
| Kalibrasyon (Platt / izotonik) ve geçici eşikler | `src/calibrate.py`, `src/calibration.py` | `models/main_model.joblib`, `models/model_card.json`, `reports/calibration_log.md`, güvenilirlik eğrisi |
| Gecikme sayısı yan denemesi | `src/check_delinq.py` | `reports/delinq_check.md` |

### Sonuçlar (28 Ekim 2026, doğrulama kümesi 2014; test açılmadı)

| Model | ROC-AUC | KS | Brier |
|---|---|---|---|
| Lojistik regresyon (3. hafta) | 0,651 | 0,219 | 0,242 |
| XGBoost, sabit parametre + erken durdurma (206 ağaç) – **ana model** | 0,656 | 0,227 | 0,114 |
| LightGBM, sabit parametre + erken durdurma (150 ağaç) | 0,656 | 0,227 | 0,114 |

Kalibrasyon: Platt (Tem–Ara 2014'te Brier 0,1168, ECE 0,009). Geçici eşikler kalibre olasılıkta 0,10 / 0,20:
Düşük %34 (batık %7,1), Orta %51 (%15,3), Yüksek %15 (%25,8). Model sürümü `xgb-fixed-platt-2026w4`.
Optuna araması (40 deneme/model, 8 çekirdek) 8 GB RAM'li dizüstünde aşırı ısınma nedeniyle durduruldu; 5. haftada hafif ayarla çalıştırılacak.

Not (macOS, Homebrew yoksa): XGBoost ve LightGBM OpenMP kitaplığı (`libomp.dylib`) ister. scikit-learn'ün kendi kopyası bağlanabilir:

```bash
ln -sf "$PWD/.venv/lib/python3.12/site-packages/sklearn/.dylibs/libomp.dylib" "$(.venv/bin/python -c 'import sys;print(sys.base_prefix)')/lib/libomp.dylib"
```

## Haftalık ilerleme

- Hafta 1: Proje planı, 7 iş paketi, H1–H8 hedefleri
- Hafta 2: İP 2 veri hazırlama
- Hafta 3: İP 3 ilk yarı – ön işleme hattı, lojistik regresyon temel çizgisi, FastAPI / Next.js iskeletleri
- Hafta 4: İP 3 ikinci yarı – XGBoost / LightGBM (erken durdurma), Platt kalibrasyonu, kalibre eşikler; veritabanı katmanı (SQLAlchemy, SQLite / PostgreSQL) ve başvuru geçmişi uç noktaları; ön yüz form / sonuç / geçmiş sayfaları; gecikme sayısı yan denemesi
- Hafta 5 (plan): Optuna araması (hafif ayar) ve ek değişkenler; İP 4 net kâr eğrisiyle kalıcı eşikler; PostgreSQL konteynerinde canlı test; SHAP gerekçeleri
