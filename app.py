"""
Sofiv2 - Yıldız Katalogu Analiz Web Arayüzü
=============================================
Çalıştırmak için:
    streamlit run app.py
"""
import io
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

# Turkish character support
matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
HISTORICAL = ROOT / "Historical"
MODERN = ROOT / "Modern"
PROCESSED = ROOT / "Processed"

# --- Page Config ---
st.set_page_config(
    page_title="Sofiv2 — Yıldız Katalogu Analizi",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Helper Functions ---
@st.cache_data
def load_template_csv():
    path = TEMPLATES / "star_catalog_template.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def load_fits_table(filepath):
    try:
        t = Table.read(str(filepath), format="fits")
        return t.to_pandas()
    except Exception:
        return None


@st.cache_data
def load_votable(filepath):
    try:
        t = Table.read(str(filepath), format="votable")
        return t.to_pandas()
    except Exception:
        return None


def load_catalog_file(uploaded_file):
    """Load an uploaded catalog file (CSV, FITS, or VOTable)."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith((".fits", ".fit")):
            content = uploaded_file.read()
            t = Table.read(io.BytesIO(content), format="fits")
            return t.to_pandas()
        elif name.endswith((".vot", ".votable", ".xml")):
            content = uploaded_file.read()
            t = Table.read(io.BytesIO(content), format="votable")
            return t.to_pandas()
    except Exception as e:
        st.error(f"Dosya yüklenirken hata: {e}")
    return None


def compute_coords(df, ra_col, dec_col):
    """Create SkyCoord from dataframe columns."""
    return SkyCoord(
        ra=df[ra_col].values * u.degree,
        dec=df[dec_col].values * u.degree,
        frame="icrs",
    )


def compute_separation_matrix(coords, names):
    """Compute angular separation matrix between all pairs."""
    n = len(coords)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            sep = coords[i].separation(coords[j]).degree
            matrix[i][j] = sep
            matrix[j][i] = sep
    return pd.DataFrame(matrix, index=names, columns=names)


# --- Sidebar ---
st.sidebar.title("Sofiv2")
st.sidebar.markdown("Yıldız Katalogu Analiz Aracı")

page = st.sidebar.radio(
    "Sayfa",
    ["Ana Sayfa", "Katalog Görüntüleyici", "Gökyüzü Haritası", "Karşılaştırma", "SIMBAD Sorgusu"],
)

# --- Main Pages ---

if page == "Ana Sayfa":
    st.title("Sofiv2 — Yıldız Katalogu Analizi")
    st.markdown(
        """
        Tarihi ve modern yıldız kataloglarını yükleme, inceleme,
        görselleştirme ve cross-match işlemleri için web arayüzü.

        **Sayfalar:**
        - **Katalog Görüntüleyici** — CSV, FITS, VOTable dosyalarını yükle ve incele
        - **Gökyüzü Haritası** — Yıldızları RA/Dec koordinatlarında görselleştir
        - **Karşılaştırma** — İki katalog arasında açı mesafesi ve cross-match
        - **SIMBAD Sorgusu** — Online astronomik veritabanından yıldız bilgisi çek
        """
    )

    # Quick stats
    df = load_template_csv()
    if df is not None:
        st.markdown("---")
        st.subheader("Şablon Katalog Özeti")
        col1, col2, col3 = st.columns(3)
        col1.metric("Yıldız Sayısı", len(df))
        col2.metric("Kolon Sayısı", len(df.columns))
        col3.metric("Katalog Sayısı", df["Catalog"].nunique())
        st.dataframe(df, use_container_width=True)

    # Project directory status
    st.markdown("---")
    st.subheader("Dizin Durumu")
    dirs = {
        "Historical/": HISTORICAL,
        "Modern/": MODERN,
        "Processed/": PROCESSED,
    }
    for name, path in dirs.items():
        files = list(path.glob("*")) if path.exists() else []
        data_files = [f for f in files if f.name != ".gitkeep"]
        if data_files:
            st.success(f"📁 {name} — {len(data_files)} dosya")
        else:
            st.info(f"📁 {name} — boş")


elif page == "Katalog Görüntüleyici":
    st.title("Katalog Görüntüleyici")

    tab1, tab2 = st.tabs(["Dosya Yükle", "Şablon Kataloglar"])

    with tab1:
        uploaded = st.file_uploader(
            "Katalog dosyası yükle",
            type=["csv", "fits", "fit", "vot", "votable"],
            help="CSV, FITS veya VOTable formatında dosya yükleyin",
        )
        if uploaded:
            df_uploaded = load_catalog_file(uploaded)
            if df_uploaded is not None:
                st.success(f"{len(df_uploaded)} satır, {len(df_uploaded.columns)} kolon yüklendi")
                st.dataframe(df_uploaded, use_container_width=True)

                st.subheader("İstatistikler")
                numeric_cols = df_uploaded.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.dataframe(df_uploaded[numeric_cols].describe(), use_container_width=True)

    with tab2:
        fmt = st.selectbox("Format", ["CSV", "FITS", "VOTable"])
        if fmt == "CSV":
            df = load_template_csv()
            if df is not None:
                st.dataframe(df, use_container_width=True)
        elif fmt == "FITS":
            path = TEMPLATES / "star_catalog_template.fits"
            if path.exists():
                df = load_fits_table(str(path))
                if df is not None:
                    st.dataframe(df, use_container_width=True)
            else:
                st.warning("FITS şablonu bulunamadı. `python scripts/create_template_fits.py` çalıştırın.")
        else:
            path = TEMPLATES / "star_catalog_template.vot"
            if path.exists():
                df = load_votable(str(path))
                if df is not None:
                    st.dataframe(df, use_container_width=True)
            else:
                st.warning("VOTable şablonu bulunamadı. `python scripts/create_template_fits.py` çalıştırın.")


elif page == "Gökyüzü Haritası":
    st.title("Gökyüzü Haritası")

    # Data source selection
    source = st.radio("Veri kaynağı", ["Şablon katalog", "Dosya yükle"])

    df = None
    if source == "Şablon katalog":
        df = load_template_csv()
    else:
        uploaded = st.file_uploader("Katalog yükle", type=["csv", "fits", "fit", "vot", "votable"])
        if uploaded:
            df = load_catalog_file(uploaded)

    if df is not None:
        # Column mapping
        all_cols = list(df.columns)
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)

        col1, col2, col3 = st.columns(3)
        ra_col = col1.selectbox("RA kolonu", numeric_cols, index=numeric_cols.index("RA_J2000") if "RA_J2000" in numeric_cols else 0)
        dec_col = col2.selectbox("Dec kolonu", numeric_cols, index=numeric_cols.index("Dec_J2000") if "Dec_J2000" in numeric_cols else min(1, len(numeric_cols) - 1))
        name_col = col3.selectbox("İsim kolonu", all_cols, index=all_cols.index("Star_Name") if "Star_Name" in all_cols else 0)

        mag_col = None
        if len(numeric_cols) > 2:
            mag_col = st.selectbox("Parlaklık kolonu (opsiyonel)", ["Yok"] + numeric_cols, index=numeric_cols.index("Magnitude") + 1 if "Magnitude" in numeric_cols else 0)
            if mag_col == "Yok":
                mag_col = None

        # Sky map
        fig, ax = plt.subplots(figsize=(14, 7))

        if mag_col:
            sizes = (2 - df[mag_col].clip(-2, 6)) * 80
            scatter = ax.scatter(
                df[ra_col], df[dec_col],
                s=sizes, c=df[mag_col], cmap="RdYlBu",
                edgecolors="black", linewidth=0.5, zorder=5,
            )
            plt.colorbar(scatter, ax=ax, label="Parlaklık (Magnitude)")
        else:
            ax.scatter(df[ra_col], df[dec_col], s=100, c="steelblue", edgecolors="black", linewidth=0.5, zorder=5)

        for _, row in df.iterrows():
            ax.annotate(
                str(row[name_col]),
                (row[ra_col], row[dec_col]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=9, fontweight="bold",
            )

        ax.set_xlabel("RA [derece]")
        ax.set_ylabel("Dec [derece]")
        ax.set_title("Gökyüzü Haritası")
        ax.invert_xaxis()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)

        # Galactic coords
        st.subheader("Galaktik Koordinatlar")
        coords = compute_coords(df, ra_col, dec_col)
        galactic = coords.galactic
        gal_df = pd.DataFrame({
            "İsim": df[name_col],
            "RA (derece)": df[ra_col].round(4),
            "Dec (derece)": df[dec_col].round(4),
            "l (Galaktik Boylam)": [g.l.degree for g in galactic],
            "b (Galaktik Enlem)": [g.b.degree for g in galactic],
        })
        st.dataframe(gal_df.round(4), use_container_width=True)

        # Magnitude chart
        if mag_col:
            st.subheader("Parlaklık Dağılımı")
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            colors = sns.color_palette("husl", len(df))
            ax2.barh(df[name_col].astype(str), df[mag_col], color=colors)
            ax2.set_xlabel("Parlaklık (Magnitude)")
            ax2.set_title("Yıldız Parlaklıkları")
            ax2.axvline(x=0, color="gray", linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig2)


elif page == "Karşılaştırma":
    st.title("Katalog Karşılaştırma")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Katalog 1")
        src1 = st.radio("Kaynak 1", ["Şablon", "Dosya yükle"], key="src1")
        df1 = None
        if src1 == "Şablon":
            df1 = load_template_csv()
        else:
            up1 = st.file_uploader("Dosya 1", type=["csv", "fits", "fit", "vot"], key="up1")
            if up1:
                df1 = load_catalog_file(up1)
        if df1 is not None:
            st.caption(f"{len(df1)} satır")

    with col2:
        st.subheader("Katalog 2")
        src2 = st.radio("Kaynak 2", ["Şablon", "Dosya yükle"], key="src2")
        df2 = None
        if src2 == "Şablon":
            df2 = load_template_csv()
        else:
            up2 = st.file_uploader("Dosya 2", type=["csv", "fits", "fit", "vot"], key="up2")
            if up2:
                df2 = load_catalog_file(up2)
        if df2 is not None:
            st.caption(f"{len(df2)} satır")

    if df1 is not None and df2 is not None:
        st.markdown("---")

        # Column mapping for both catalogs
        num1 = list(df1.select_dtypes(include=[np.number]).columns)
        num2 = list(df2.select_dtypes(include=[np.number]).columns)
        all1 = list(df1.columns)
        all2 = list(df2.columns)

        c1, c2, c3, c4 = st.columns(4)
        ra1 = c1.selectbox("RA 1", num1, index=num1.index("RA_J2000") if "RA_J2000" in num1 else 0)
        dec1 = c2.selectbox("Dec 1", num1, index=num1.index("Dec_J2000") if "Dec_J2000" in num1 else min(1, len(num1) - 1))
        ra2 = c3.selectbox("RA 2", num2, index=num2.index("RA_J2000") if "RA_J2000" in num2 else 0)
        dec2 = c4.selectbox("Dec 2", num2, index=num2.index("Dec_J2000") if "Dec_J2000" in num2 else min(1, len(num2) - 1))

        name1 = st.selectbox("İsim kolonu (Katalog 1)", all1, index=all1.index("Star_Name") if "Star_Name" in all1 else 0)

        # Separation matrix for catalog 1
        coords1 = compute_coords(df1, ra1, dec1)
        names1 = df1[name1].astype(str).tolist()
        sep_df = compute_separation_matrix(coords1, names1)

        st.subheader("Açı Mesafe Matrisi (Katalog 1)")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(sep_df.round(1), annot=True, fmt=".1f", cmap="YlOrRd", ax=ax, square=True)
        ax.set_title("Açı Mesafe Matrisi (derece)")
        plt.tight_layout()
        st.pyplot(fig)

        # Cross-match
        st.subheader("Cross-Match")
        threshold = st.slider("Eşleşme eşiği (arcsec)", 1.0, 60.0, 5.0, 0.5)

        coords2 = compute_coords(df2, ra2, dec2)
        idx, sep2d, _ = coords1.match_to_catalog_sky(coords2)

        matches = []
        for i in range(len(coords1)):
            sep_arcsec = sep2d[i].arcsecond
            if sep_arcsec <= threshold:
                matches.append({
                    "Katalog 1": names1[i],
                    "Katalog 2 Eşleşme": idx[i],
                    "Mesafe (arcsec)": round(sep_arcsec, 3),
                })

        if matches:
            st.success(f"{len(matches)} eşleşme bulundu ({threshold}\" eşik)")
            st.dataframe(pd.DataFrame(matches), use_container_width=True)
        else:
            st.warning(f"{threshold}\" eşik değerinde eşleşme bulunamadı.")


elif page == "SIMBAD Sorgusu":
    st.title("SIMBAD Sorgusu")
    st.caption("Astronomik veritabanından yıldız bilgisi çek (internet gerektirir)")

    query_type = st.radio("Sorgu tipi", ["İsimle Ara", "Bölge Araması (Cone Search)"])

    if query_type == "İsimle Ara":
        star_name = st.text_input("Yıldız adı", value="Sirius")
        if st.button("Sorgula") and star_name:
            with st.spinner("SIMBAD sorgulanıyor..."):
                try:
                    from astroquery.simbad import Simbad
                    result = Simbad.query_object(star_name)
                    if result is not None:
                        st.success(f"'{star_name}' bulundu!")
                        st.dataframe(result.to_pandas(), use_container_width=True)
                    else:
                        st.warning(f"'{star_name}' bulunamadı.")
                except Exception as e:
                    st.error(f"Sorgu hatası: {e}")

    else:
        col1, col2, col3 = st.columns(3)
        ra_input = col1.number_input("RA (derece)", value=101.2871, format="%.4f")
        dec_input = col2.number_input("Dec (derece)", value=-16.7161, format="%.4f")
        radius = col3.number_input("Yarıçap (derece)", value=0.1, min_value=0.01, max_value=5.0, format="%.2f")

        if st.button("Bölge Sorgula"):
            with st.spinner("SIMBAD sorgulanıyor..."):
                try:
                    from astroquery.simbad import Simbad
                    center = SkyCoord(ra=ra_input * u.degree, dec=dec_input * u.degree, frame="icrs")
                    result = Simbad.query_region(center, radius=radius * u.degree)
                    if result is not None:
                        result_df = result.to_pandas()
                        st.success(f"{len(result_df)} nesne bulundu ({radius}° yarıçap)")
                        st.dataframe(result_df, use_container_width=True)
                    else:
                        st.warning("Sonuç bulunamadı.")
                except Exception as e:
                    st.error(f"Sorgu hatası: {e}")


# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("Sofiv2 — Astronomi Veri Analiz Çalışma Alanı")
