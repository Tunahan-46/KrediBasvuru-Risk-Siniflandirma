# Zamana göre bölme günlüğü (src/split_time.py)

| Küme | Kayıt | Batık oranı | Not |
|---|---|---|---|
| Eğitim (2007–2013) | 172,988 | 12.43 % | Ön işleme parametreleri buradan öğrenilir |
| Doğrulama (2014) | 162,570 | 13.73 % | Hiperparametre ve eşik seçimi |
| Test (2015) | 283,026 | 14.89 % | Kilitli; dönem sonunda bir kez açılacak |
| Toplam | 618,584 | 13.90 % |  |

Çıktılar: `data/processed/train.parquet`, `valid.parquet`, `test.parquet`

Not: test.parquet modelleme bitene kadar hiçbir betik veya defter tarafından okunmaz.
