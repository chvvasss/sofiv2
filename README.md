# Sofiv2 - Astronomi Veri Analiz Çalışma Alanı

Yıldız kataloglarının karşılaştırmalı analizi için Python ve TOPCAT/STILTS tabanlı çalışma alanı.

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
└── tests/             Test ve doğrulama betikleri
```

## Kurulum

### Python Ortamı

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
# veya: .venv\Scripts\activate  # Windows (CMD)
pip install -r requirements.txt
```

### Şablon Tabloları Oluşturma

```bash
python scripts/create_template_fits.py
```

Bu komut `templates/` altında FITS ve VOTable formatlarında şablon dosyalar üretir.

### TOPCAT / STILTS

```bash
tools\topcat.bat                # GUI başlatır
tools\stilts.bat tpipe ...      # Komut satırı
```

Portable OpenJDK 21 JRE `tools/java/` dizininde bulunur. Sistem geneli Java kurulumu gerekmez.

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

## Testleri Çalıştırma

```bash
python tests/test_packages.py
```

## Referanslar

- Astropy Collaboration, *Astropy: A Community Python Library for Astronomy* (2013)
- Taylor, M., *TOPCAT & STIL: Tools for Astronomical Tables* (2005)
