# Maç Analiz v1

Basit Streamlit arayüzüyle günlük futbol maçlarını gol marketlerine göre sıralar.

## Veri nereden geliyor?

Canlı modda **Sportmonks Football API v3** kullanılır.

Uygulama iki veri grubunu çeker:

1. Seçilen tarihin fikstürü:
   `GET /v3/football/fixtures/date/YYYY-MM-DD`
2. Seçilen tarihten önceki geçmiş sonuçlar:
   `GET /v3/football/fixtures/between/START/END`

`participants`, `scores` ve `league` ilişkileri dahil edilir. Sonuçlarda `scores` içindeki
`CURRENT` skoru kullanılır.

Bu sürüm Maçkolik'ten scraping yapmaz.

## Analiz mantığı

Her maç için iki takımın son N maçı incelenir.

Marketler:
- 1.5 Üst
- 2.5 Üst
- 3.5 Alt
- KG Var
- KG Yok

Ağırlıklar:
- Ev sahibi genel son maçlar: %35
- Deplasman genel son maçlar: %35
- Ev sahibinin iç saha örneği: %15
- Deplasmanın deplasman örneği: %15

Küçük örneklemlerin aşırı %0 / %100 üretmesini engellemek için oranlar %50'ye doğru
yumuşatılır. Bu bir istatistiksel aday sıralama aracıdır; garanti tahmin değildir.

## Kurulum

Python 3.11+ önerilir.

Windows Terminal / PowerShell:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcı otomatik açılmazsa:
`http://localhost:8501`

## Sportmonks token

Sportmonks hesabından API token oluşturup programın sol paneline yapıştır.

Token yoksa **Demo Modu** açıktır; arayüz ve hesaplama örnek verilerle çalışır.

## Sonraki sürüm fikirleri

- Lig bazında kalıcı favoriler
- 0.5 ilk yarı üst
- Takım golü 0.5 / 1.5
- H2H etkisi
- xG ve şut istatistikleri
- Sportmonks prediction ile kendi model sonucunu yan yana gösterme
- SQLite cache (API kotasını koruma)
- CSV/Excel dışa aktarma
