# Star S — Star Catalog Analysis Dashboard

Yildiz kataloglarinin karsilastirmali analizi icin web tabanli dashboard. Dash + Plotly ile interaktif grafikler, Astropy ile koordinat donusumleri, SIMBAD ile online veri sorgulama.

**Canlı Demo:** [sofiv2.onrender.com](https://sofiv2.onrender.com)

---

## Kurulum

```bash
git clone https://github.com/chvvasss/sofiv2.git
cd sofiv2
python setup.py
```

Setup otomatik olarak:
- `.venv/` sanal ortam olusturur
- Tum paketleri kurar (astropy, pandas, plotly, dash, scipy, astroquery)
- TOPCAT, STILTS ve portable OpenJDK indirir
- Sablon FITS/VOTable dosyalarini uretir
- Dogrulama testlerini calistirir

## Calistirma

```bash
# Ortami aktifle
source .venv/Scripts/activate   # Windows (Git Bash)
.venv\Scripts\activate          # Windows (CMD)
source .venv/bin/activate       # Linux/macOS

# Web dashboard
python app.py
# Tarayicide http://localhost:8050 ac

# Jupyter Notebook (interaktif analiz)
jupyter notebook notebooks/analysis.ipynb

# TOPCAT GUI
tools/topcat.bat
```

---

## Sayfa Rehberi

Dashboard 7 sayfadan olusur. Sol sidebar'dan gezinebilirsin.

### 1. Dashboard

Ana sayfa — genel bakis.

| Bolum | Aciklama |
|-------|----------|
| **Istatistik Kartlari** | Yildiz sayisi, katalog sayisi, desteklenen formatlar, ortalama parlaklik |
| **Gokyuzu Onizleme** | Sablon katalogdaki yildizlarin RA/Dec haritasi (Plotly scatter) |
| **Dizin Durumu** | Historical/, Modern/, Processed/ klasorlerindeki dosya sayilari |
| **Hizli Baslangic** | 4 adimlik is akisi rehberi |

### 2. Catalog Viewer

Dosya yukleme ve tablo goruntuleyici.

**Dosya Yukle sekmesi:**
- CSV, FITS veya VOTable dosyasi surukle-birak veya sec
- Yuklenen dosya otomatik parse edilir ve tablo olarak gosterilir
- Kolonlar siralama ve filtreleme destekler

**Sablon Kataloglar sekmesi:**
- `templates/star_catalog_template.csv` icerigini goruntuler
- 5 yildiz: Sirius, Vega, Betelgeuse, Polaris, Aldebaran
- 11 kolon: Star_Name, Catalog, RA_orig, Dec_orig, RA_J2000, Dec_J2000, Magnitude, Band, Epoch, Notes, Reference

### 3. Data Report

Tum verilerin detayli beyaz formatta raporu.

| Bolum | Aciklama |
|-------|----------|
| **Indirme Cubugu** | CSV, JSON ve CSV+Galaktik olarak 3 format indirme |
| **Tam Veri Tablosu** | Tum yildizlar, siralama/filtreleme, beyaz tema |
| **Kolon Istatistikleri** | Her sayisal kolon icin Count, Min, Max, Mean, Std, Median |
| **Veri Tamliligi** | Kolon bazinda dolulik orani — renkli progress bar'lar |
| **Yildiz Detaylari** | Her yildiz icin ayri kart — tum alanlar + galaktik koordinatlar |
| **Koordinat Referansi** | ICRS sistemi, epoch, hassasiyet, donusum bilgileri |

**Indirme formatlari:**
- **CSV** — standart tablo (`stars_catalog.csv`)
- **JSON** — API uyumlu format (`stars_catalog.json`)
- **CSV + Galaktik** — l/b galaktik koordinatlar eklenmis (`stars_catalog_full.csv`)

### 4. Sky Map

Interaktif gokyuzu haritasi.

- Plotly scatter: x=RA, y=Dec
- Boyut: parlakliga gore (parlak yildiz = buyuk nokta)
- Renk: magnitude colorscale (kirmizi → mavi)
- Hover: yildiz adi, RA, Dec, magnitude
- Zoom, pan, export destegi
- **Galaktik Koordinatlar** tablosu: Astropy SkyCoord ile ICRS → Galaktik donusum

### 5. Magnitude Analysis

Parlaklik analizi — 3 grafik + istatistik.

| Grafik | Aciklama |
|--------|----------|
| **Bar Chart** | Yildizlar parlaklik sirasina gore — yatay bar |
| **Histogram** | Magnitude dagilimi — 15 bin |
| **Box Plot** | Kataloglara gore parlaklik dagilimi |
| **Istatistik Kartlari** | Min, Ortalama, Medyan, Max degerleri |

### 6. Cross-Match

Katalog ici aci mesafe analizi.

- **Heatmap** — tum yildiz ciftleri arasi aci mesafe matrisi (derece)
- **Mesafe Tablosu** — her cift icin arcsecond ve degree degerleri
- Siralama: en yakin ciftler uste gelir
- Hesaplama: `SkyCoord.separation()` ile gercek gokyuzu acisi

### 7. SIMBAD Query

Online astronomik veritabani sorgusu (internet gerektirir).

**Isimle Ara:**
- Yildiz adini yaz (ornegin "Sirius", "Vega", "M31")
- SIMBAD veritabanindan koordinat, tip, parlaklik bilgisi doner

**Bolge Aramasi (Cone Search):**
- Merkez RA/Dec ve yaricap (derece) gir
- Belirtilen bolgede bulunan tum nesneleri listeler
- Sonuclari gokyuzu haritasinda gosterir

---

## Desteklenen Dosya Formatlari

| Format | Uzanti | Aciklama |
|--------|--------|----------|
| CSV | `.csv` | Virgul ayrikli tablo — en yaygin |
| FITS | `.fits`, `.fit` | Flexible Image Transport System — astronomi standardi |
| VOTable | `.vot`, `.votable`, `.xml` | Virtual Observatory tablo formati |

## Kolon Otomatik Algilama

Dosya yuklendiginde sistem su kolonlari otomatik bulur:

| Alan | Aranan Pattern'ler |
|------|-------------------|
| RA | `ra_j2000`, `ra_2000`, `ra`, `right_ascension` |
| Dec | `dec_j2000`, `dec_2000`, `dec`, `declination` |
| Magnitude | `magnitude`, `mag`, `vmag`, `gmag` |
| Name | `star_name`, `name`, `main_id`, `designation` |

Eger bulunamazsa ilk sayisal kolonlar RA/Dec/Mag olarak atanir.

---

## Proje Yapisi

```
star-s/
├── app.py                  Ana Dash uygulamasi (~1170 satir)
├── assets/
│   └── style.css           Dark space theme CSS (~700 satir)
├── templates/
│   └── star_catalog_template.csv   5 yildiz sablon katalog
├── notebooks/
│   └── analysis.ipynb      Jupyter interaktif analiz
├── Historical/             Tarihi kataloglar (Tycho, Hipparcos)
├── Modern/                 Gaia DR3, SDSS, Pan-STARRS
├── Processed/              Temizlenmis veri setleri
├── Visualizations/         Plotlar, grafikler
├── Documentation/          Metodoloji, referanslar
├── scripts/                Python betikleri
├── tools/                  TOPCAT, STILTS, portable Java
├── tests/                  Test betikleri
├── requirements.txt        Tum bagimliliklar (gelistirme)
├── requirements-deploy.txt Sadece deploy bagimliliklari
├── render.yaml             Render.com deploy konfigurasyonu
├── setup.py                Tek komutla kurulum betigi
└── .gitignore
```

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Frontend | Dash + Plotly, custom CSS dark theme |
| Backend | Python, Gunicorn (production) |
| Astronomi | Astropy (koordinat), Astroquery (SIMBAD) |
| Veri | Pandas, NumPy, SciPy |
| Deploy | Render.com (free tier) |
| Araclar | TOPCAT, STILTS (tablo gorsellestirme) |

## Deploy

Render.com uzerinde ucretsiz deploy:

1. [render.com](https://render.com) — GitHub ile giris
2. New Web Service → `chvvasss/sofiv2` repo sec
3. Build: `pip install -r requirements-deploy.txt`
4. Start: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Env var: `RENDER=true`
6. Instance: Free

Her `git push` otomatik redeploy tetikler.

## Referanslar

- Astropy Collaboration, *Astropy: A Community Python Library for Astronomy* (2013)
- Taylor, M., *TOPCAT & STIL: Tools for Astronomical Tables* (2005)
- Wenger et al., *The SIMBAD Astronomical Database* (2000)
