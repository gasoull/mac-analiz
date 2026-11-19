# ONUR ANALİZ — Canlı Maç Merkezi

Bu klasör, daha sade bir canlı skor ve maç listesi uygulamasıdır. Varsayılan olarak ESPN'in herkese açık ancak resmî destek/garanti sunmayan skor uç noktalarını kullanır. API anahtarı gerekmez.

## Streamlit Cloud
1. GitHub deposunda `app.py` ve `requirements.txt` dosyalarını güncelleyin (önce eski dosyaları yedekleyin).
2. Streamlit Cloud uygulama ayarlarında Main file path `app.py` olsun.
3. Deploy/Reboot yapın.

## Özellikler
- Günlük maçlar ve lig grupları
- Canlı skor, maç durumu ve takım araması
- Otomatik yenileme (60 sn) ve manuel yenileme
- Maç detay linki, Türkiye saati

Not: ESPN maç kapsamı Maçkolik ile aynı değildir. Maç tahminleri bu sürüme eklenmemiştir. Üçüncü taraf API zaman zaman erişilemez olabilir.
