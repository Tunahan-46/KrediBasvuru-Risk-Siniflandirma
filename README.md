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
src/               Veri hazırlama betikleri
notebooks/         Keşifsel analiz defteri
reports/           EDA özeti ve grafikler
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

## Haftalık ilerleme

- Hafta 1: Proje planı, 7 iş paketi, H1–H8 hedefleri
- Hafta 2: İP 2 veri hazırlama (bu depo)
- Hafta 3: Ön işleme Pipeline, lojistik regresyon temel çizgisi, FastAPI / Next.js iskeletleri
