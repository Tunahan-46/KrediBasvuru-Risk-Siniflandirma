# Keşifsel analiz özeti (eğitim + doğrulama; test kapalı)

## 1. Sınıf dengesi

| kume | kayit | batik_orani |
|---|---|---|
| dogrulama | 162,570 | 13.73 |
| egitim | 172,988 | 12.43 |

Toplam batık oranı: **13.06 %**. Batık krediler azınlıkta; eğitimde sınıf ağırlığı, değerlendirmede ROC-AUC ve KS kullanılacak.

## 2. Eksik değer oranları (%)

| sutun | eksik_yuzde |
|---|---|
| emp_length | 5.12 |
| revol_util | 0.07 |

Karar: sayısal eksikler eğitim kümesinin medyanıyla, kategorik eksikler 'bilinmiyor' seviyesiyle doldurulacak.

## 3. Batık oranının yıla göre dağılımı

| issue_year | kayit | batik_orani |
|---|---|---|
| 2007 | 251 | 17.93 |
| 2008 | 1,562 | 15.81 |
| 2009 | 4,716 | 12.60 |
| 2010 | 8,466 | 9.95 |
| 2011 | 14,101 | 10.63 |
| 2012 | 43,470 | 13.58 |
| 2013 | 100,422 | 12.33 |
| 2014 | 162,570 | 13.73 |

## 4. Batık oranının FICO aralığına göre dağılımı

| fico_aralik | kayit | batik_orani |
|---|---|---|
| [600, 660) | 2 | 0.00 |
| [660, 680) | 111,255 | 17.24 |
| [680, 700) | 93,082 | 14.08 |
| [700, 720) | 61,882 | 10.82 |
| [720, 750) | 42,833 | 8.11 |
| [750, 850) | 26,504 | 5.17 |

## 5. Batık oranının kredi amacına göre dağılımı

| purpose | kayit | batik_orani |
|---|---|---|
| small_business | 4,979 | 22.09 |
| moving | 2,561 | 18.04 |
| renewable_energy | 285 | 16.84 |
| medical | 3,764 | 16.23 |
| educational | 309 | 15.86 |
| other | 18,481 | 15.48 |
| vacation | 2,241 | 14.90 |
| house | 1,572 | 14.89 |
| debt_consolidation | 189,828 | 13.59 |
| home_improvement | 18,487 | 11.32 |
| credit_card | 79,435 | 11.05 |
| wedding | 1,900 | 11.00 |
| major_purchase | 7,582 | 10.96 |
| car | 4,134 | 10.16 |

## 6. Batık oranının borç/gelir oranına göre dağılımı

| dti_aralik | kayit | batik_orani |
|---|---|---|
| [0, 10) | 71,626 | 10.29 |
| [10, 15) | 74,847 | 11.25 |
| [15, 20) | 74,803 | 12.97 |
| [20, 25) | 59,466 | 14.70 |
| [25, 30) | 36,307 | 16.93 |
| [30, 100) | 18,509 | 18.58 |

## 7. Sayısal değişkenlerin dağılımı

| sutun | count | mean | 1% | 50% | 99% | max |
|---|---|---|---|---|---|---|
| loan_amnt | 335,558 | 12233.50 | 1500.00 | 10000.00 | 35000.00 | 35000.00 |
| annual_inc | 335,558 | 70902.89 | 17463.77 | 60000.00 | 240000.00 | 7500000.00 |
| dti | 335,558 | 16.79 | 1.57 | 16.36 | 34.51 | 39.99 |
| fico_range_low | 335,558 | 696.36 | 660.00 | 690.00 | 795.00 | 845.00 |
| open_acc | 335,558 | 10.96 | 3.00 | 10.00 | 26.00 | 84.00 |
| delinq_2yrs | 335,558 | 0.28 | 0.00 | 0.00 | 4.00 | 29.00 |
| revol_util | 335,337 | 54.96 | 1.60 | 56.10 | 97.70 | 892.30 |
| inq_last_6mths | 335,558 | 0.77 | 0.00 | 0.00 | 4.00 | 8.00 |
| tutar_gelir | 335,558 | 0.20 | 0.03 | 0.18 | 0.45 | 0.83 |

Gözlem: annual_inc sütununda %99 ile max arasındaki fark büyükse logaritma ve %99 kırpma kararı geçerlidir.

## 8. Metin biçimli sütun örneği: emp_length

| emp_length | kayit |
|---|---|
| 10+ years | 100,696 |
| 2 years | 30,980 |
| < 1 year | 27,397 |
| 3 years | 27,346 |
| 5 years | 22,598 |
| 1 year | 22,445 |
| 4 years | 20,845 |
| 6 years | 19,003 |
| 7 years | 18,648 |
| <eksik> | 17,179 |
| 8 years | 15,958 |
| 9 years | 12,463 |

Karar: '< 1 year' -> 0, '10+ years' -> 10, eksik -> ayrı seviye (bkz. data/variable_dictionary.csv).

## Üretilen çizimler

- `figures/batik_orani_amac.png`
- `figures/batik_orani_fico.png`
- `figures/batik_orani_yil.png`
- `figures/dagilimlar.png`
