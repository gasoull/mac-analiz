# ONUR ANALİZ · Premium Canlı Maç Merkezi

Örnek/sahte maç bulunmaz. Streamlit üzerinde gerçek veriyle çalışan premium koyu temalı maç listesi.

## Veri kaynakları

1. [SportScore](https://sportscore.com/developers/api/) — `/api/v1/fixtures/?sport=football&date=YYYY-MM-DD&limit=200`, bugün için ayrıca `/api/widget/matches/?sport=football&limit=50`.
2. [TheSportsDB](https://www.thesportsdb.com/docs/api) — ilk kaynak verisiz/hatalıysa `eventsday.php?d=YYYY-MM-DD&s=Soccer`.

**Önemli:** Ücretsiz kaynaklar tüm ligleri, her tarihi ya da saniyelik canlı skorları garanti etmez. TheSportsDB ücretsiz verisi sınırlı olabilir. Hatalarda gösterilen skorlar uydurulmaz. Kaynak erişimi çalıştırılan Streamlit sunucusunun ağına bağlıdır.

## GitHub ve Streamlit Cloud

1. Mevcut GitHub deposundaki dosyalarını yedekle.
2. Bu ZIP içindeki `app.py`, `data_sources.py`, `requirements.txt` ve `README.md` dosyalarını `main` dalının **kök dizinine** yükle.
3. Eski `app.py` dosyasını yenisiyle **Replace** yap; ana çalıştırma dosyası `app.py` kalmalı.
4. Streamlit Cloud > uygulama ayarları > Main file path: `app.py`.
5. GitHub değişiklikleri yayınlandıktan sonra gerekirse **Reboot app** yap.

## Yerelde çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Kullanım

- Dün / Bugün / Yarın veya tarih seç.
- Takım/lig arama, lig seçimi, canlı/biten/yaklaşan filtreleri.
- `Yenile` butonu veriyi tekrar çeker. Sayfa yaklaşık 75 saniyede bir otomatik yenilenir; API sonucu 65 saniye saklanır.

## Sınırlamalar

- Bazı servislerin tarihi UTC olarak ele alması Türkiye gününde gece yakınındaki bazı maçları eksik gösterebilir.
- Match detail / tahmin algoritması bu sürümde yok; öncelik sağlam veri / düzgün maç listesi.
- SportScore'un kullanım şartları gereği kaynak adı ve bağlantısı görünür şekilde eklenmiştir.
