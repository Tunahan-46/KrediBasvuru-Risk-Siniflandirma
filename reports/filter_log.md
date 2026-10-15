# Süzme günlüğü (src/filter_data.py)

Girdi: `data/raw/accepted_2007_to_2018Q4.csv`

| Adım | Kayıt sayısı |
|---|---|
| Ham veri (tüm satırlar) | 2,260,701 |
| Geçerli kayıt (özet satırları atıldı) | 2,260,668 |
| 36 ay vadeli | 1,609,754 |
| 2007–2015 arası verilmiş | 621,169 |
| Sonucu kesin (Fully Paid / Charged Off) | 618,584 |

Batık oranı (çalışma kümesi): **13.90 %**

## Yıla göre kayıt sayısı

| Yıl | Kayıt |
|---|---|
| 2007 | 251 |
| 2008 | 1,562 |
| 2009 | 4,716 |
| 2010 | 8,466 |
| 2011 | 14,101 |
| 2012 | 43,470 |
| 2013 | 100,422 |
| 2014 | 162,570 |
| 2015 | 283,026 |

Çıktılar: `data/processed/loans_filtered.parquet` (model sütunları), `data/processed/lender_grade.parquet` (kurum notu, modele verilmez)
