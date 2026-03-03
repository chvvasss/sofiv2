# Sofiv2 - Astronomi Veri Analiz Çalışma Alanı

Yıldız kataloglarının karşılaştırmalı analizi için Python ve TOPCAT/STILTS tabanlı çalışma alanı.

## Hızlı Başlangıç

Repo'yu klonladıktan sonra **tek komutla** tüm ortamı kurabilirsiniz:

```bash
git clone https://github.com/chvvasss/sofiv2.git
cd sofiv2
python setup.py
```

Bu komut otomatik olarak:
- Python sanal ortamı oluşturur (`.venv/`)
- Tüm paketleri kurar (astropy, pandas, numpy, matplotlib, seaborn, astroquery, scipy, jupyter)
- TOPCAT, STILTS ve portable OpenJDK indirir
- Şablon FITS/VOTable dosyalarını üretir
- Doğrulama testlerini çalıştırır

## Kullanım

```bash
# Ortamı aktifleştir
source .venv/Scripts/activate   # Windows (Git Bash)
.venv\Scripts\activate          # Windows (CMD)
source .venv/bin/activate       # Linux/macOS

# Web arayüzü (tarayıcıda dashboard)
streamlit run app.py

# Jupyter Notebook aç (interaktif analiz)
jupyter notebook notebooks/analysis.ipynb

# TOPCAT GUI aç (tablo görselleştirme ve cross-match)
tools\topcat.bat

# STILTS komut satırı (büyük tablo işlemleri)
tools\stilts.bat tpipe in=templates/star_catalog_template.csv ifmt=csv omode=stats
```

## Proje Yapısı

```
sofiv2/
├── Historical/        Ham kataloglar (Tycho, Hipparcos vb.)
├── Modern/            Gaia DR3, SDSS, Pan-STARRS verileri
├── Processed/         Temizlenmiş veri setleri, ara tablolar
├── Visualizations/    Plotlar, grafikler, heatmap'ler
├── Documentation/     Metodoloji, referanslar, iş akışı notları
├── scripts/           Python betikleri
├── templates/         Şablon tablolar (CSV, FITS, VOTable)
├── tools/             TOPCAT, STILTS, portable Java
├── notebooks/         Jupyter Notebook'lar
└── tests/             Test ve doğrulama betikleri
```

## Şablon Tablo Kolonları

| Kolon | Açıklama |
|-------|----------|
| Star_Name | Yıldız adı |
| Catalog | Kaynak katalog |
| RA_orig | Orijinal RA (derece) |
| Dec_orig | Orijinal Dec (derece) |
| RA_J2000 | J2000 epok RA (derece) |
| Dec_J2000 | J2000 epok Dec (derece) |
| Magnitude | Parlaklık değeri |
| Band | Fotometrik bant (V, G, r, g vb.) |
| Epoch | Gözlem epoku |
| Notes | Ek notlar |
| Reference | Katalog referansı |

## Testler

```bash
python tests/test_packages.py
```

## Referanslar

- Astropy Collaboration, *Astropy: A Community Python Library for Astronomy* (2013)
- Taylor, M., *TOPCAT & STIL: Tools for Astronomical Tables* (2005)
