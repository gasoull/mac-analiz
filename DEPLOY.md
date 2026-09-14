# İnternetten Açılan Sürüm — Yayınlama

Bu klasör Streamlit Community Cloud'a yüklenmeye hazırdır.

## 1) GitHub
- GitHub hesabı aç / giriş yap.
- Yeni bir repository oluştur. Örn: `mac-analiz`
- Bu klasördeki dosyaları repository'nin köküne yükle.

## 2) Streamlit Community Cloud
- `https://share.streamlit.io` adresine GitHub ile giriş yap.
- **Create app** seç.
- GitHub repository olarak `mac-analiz` seç.
- Main file path: `app.py`
- İstersen URL adını belirle.

## 3) API anahtarını güvenli ekle
Deploy ekranında **Advanced settings > Secrets** alanına:

```toml
SPORTMONKS_API_TOKEN = "SENIN_GERCEK_TOKENIN"
```

yaz.

Token'ı GitHub dosyasının içine YAZMA.

## 4) Deploy
Deploy'a bastığında uygulaman:
`https://...streamlit.app`
şeklinde bir internet adresinden açılır.

Telefon, tablet ve bilgisayardan ekstra program kurmadan kullanılabilir.

## Not
Sportmonks aboneliğinde erişilemeyen lig/istatistik varsa uygulama o veriyi alamaz.
Demo modu API olmadan arayüzü test etmek içindir.
