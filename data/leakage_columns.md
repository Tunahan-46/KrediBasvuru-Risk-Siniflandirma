# Sızıntı sütunu listesi

Ölçüt: "Bu değer kredi onaylanmadan önce biliniyor muydu?" Yanıtı **hayır** olan
sütunlar modele verilmez. Kaynak: Kaufman vd. (2012), Leakage in data mining.

## A. Kredi verildikten sonra oluşan sütunlar

| Sütun | Neden sızıntı |
|---|---|
| total_pymnt, total_pymnt_inv | Toplam ödeme; batık kredide düşüktür |
| total_rec_prncp, total_rec_int, total_rec_late_fee | Tahsil edilen anapara / faiz / gecikme ücreti |
| recoveries, collection_recovery_fee | Yalnızca batık kredilerde sıfırdan büyük |
| last_pymnt_d, last_pymnt_amnt, next_pymnt_d | Ödeme takvimi bilgisi |
| out_prncp, out_prncp_inv | Kalan anapara |
| last_credit_pull_d | Kredi onayından sonraki sorgu tarihi |
| funded_amnt, funded_amnt_inv | Yatırımcı fonlaması, onay sonrası |
| hardship_* (tüm sütunlar) | Ödeme zorluğu planı, onay sonrası |
| settlement_*, debt_settlement_flag | Borç yapılandırma, onay sonrası |
| pymnt_plan | Ödeme planı değişikliği |

## B. Kurumun kendi risk değerlendirmesini taşıyan sütunlar

| Sütun | Neden |
|---|---|
| grade, sub_grade | Lending Club'ın notu; H4 karşılaştırması için ayrı dosyada tutulur |
| int_rate | Nota göre belirlenen faiz |
| installment | Faiz ve tutardan türetilir |

## C. Dönemler arası bilgi farkı yaratan sütunlar

2007–2011 kayıtlarında büyük oranda boş olan ya da sonraki yıllarda toplanmaya başlanan
sütunlar (ör. `sec_app_*`, `verification_status_joint`, `annual_inc_joint`, `dti_joint`,
`revol_bal_joint`, `il_util`, `open_acc_6m`, `mths_since_rcnt_il`) kullanılmaz; aksi hâlde
eğitim (2007–2013) ve test (2015) dönemleri arasında bilgi farkı oluşur.

## Şüpheli görülüp temkinle çıkarılanlar

`funded_amnt_inv` ve `last_credit_pull_d` başvuru anında bilinip bilinmediği tartışmalı
bulundu; her ikisi de çıkarıldı.
