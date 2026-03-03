"""
Sofiv2 - Yildiz Katalogu Analiz Web Arayuzu (Premium Edition)
==============================================================
Dark space theme, Plotly interactive charts, session state.

Run:
    streamlit run app.py
"""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
HISTORICAL = ROOT / "Historical"
MODERN = ROOT / "Modern"
PROCESSED = ROOT / "Processed"

# --- Page Config ---
st.set_page_config(
    page_title="Sofiv2 — Yildiz Katalogu Analizi",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===================== CSS THEME =====================
def inject_css():
    st.markdown(
        """
        <style>
        /* Main background */
        .stApp {
            background: linear-gradient(165deg, #0a0a2e 0%, #060620 40%, #000011 100%);
            color: #e0e0e0;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d0d35 0%, #060618 100%);
            border-right: 1px solid rgba(240,192,64,0.2);
        }
        section[data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #f0c040 !important;
        }
        section[data-testid="stSidebar"] .stRadio label {
            color: #c0c0d0 !important;
        }

        /* Headers */
        h1, h2, h3 { color: #f0c040 !important; }
        h1 { text-shadow: 0 0 20px rgba(240,192,64,0.3); }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: rgba(15, 15, 40, 0.8);
            border: 1px solid rgba(79, 195, 247, 0.3);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 0 15px rgba(79, 195, 247, 0.1);
        }
        div[data-testid="stMetric"] label {
            color: #4fc3f7 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700;
        }

        /* DataFrames */
        .stDataFrame {
            border: 1px solid rgba(79, 195, 247, 0.2);
            border-radius: 8px;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #1a1a50, #0d0d35);
            color: #f0c040;
            border: 1px solid rgba(240, 192, 64, 0.4);
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            border-color: #f0c040;
            box-shadow: 0 0 15px rgba(240, 192, 64, 0.3);
            color: #ffffff;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(15, 15, 40, 0.6);
            border-radius: 8px 8px 0 0;
            color: #c0c0d0;
            border: 1px solid rgba(79, 195, 247, 0.2);
        }
        .stTabs [aria-selected="true"] {
            background: rgba(79, 195, 247, 0.15);
            color: #4fc3f7 !important;
            border-color: #4fc3f7;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background: rgba(15, 15, 40, 0.6);
            border-radius: 8px;
            color: #4fc3f7 !important;
        }

        /* File uploader */
        section[data-testid="stFileUploader"] {
            border: 1px dashed rgba(240, 192, 64, 0.3);
            border-radius: 12px;
            padding: 8px;
        }

        /* Slider */
        .stSlider > div > div > div > div {
            background-color: #f0c040 !important;
        }

        /* Success/Info/Warning/Error */
        .stSuccess { border-left-color: #4fc3f7 !important; }
        .stInfo { border-left-color: #f0c040 !important; }

        /* Divider */
        hr { border-color: rgba(240, 192, 64, 0.15) !important; }

        /* Card container helper */
        .glass-card {
            background: rgba(15, 15, 40, 0.75);
            border: 1px solid rgba(79, 195, 247, 0.2);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 16px;
            backdrop-filter: blur(10px);
        }
        .glass-card h3 { margin-top: 0; }

        /* Guide cards */
        .guide-card {
            background: rgba(15, 15, 40, 0.6);
            border: 1px solid rgba(240, 192, 64, 0.15);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
        }
        .guide-card h4 { color: #f0c040; margin: 8px 0 4px; }
        .guide-card p { color: #a0a0b8; font-size: 0.85rem; margin: 0; }

        /* Hide default streamlit footer */
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ===================== PLOTLY THEME =====================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(10,10,46,0.0)",
    plot_bgcolor="rgba(10,10,46,0.4)",
    font=dict(color="#c0c0d0", family="DejaVu Sans"),
    title_font=dict(color="#f0c040", size=18),
    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(79,195,247,0.3)"),
    xaxis=dict(gridcolor="rgba(79,195,247,0.1)", zerolinecolor="rgba(79,195,247,0.2)"),
    yaxis=dict(gridcolor="rgba(79,195,247,0.1)", zerolinecolor="rgba(79,195,247,0.2)"),
    margin=dict(l=60, r=30, t=50, b=50),
)

STAR_COLORSCALE = [
    [0.0, "#ff4444"],   # bright red (negative mag — very bright)
    [0.3, "#ffaa22"],   # orange
    [0.5, "#f0c040"],   # gold
    [0.7, "#88ccff"],   # light blue
    [1.0, "#2266cc"],   # deep blue (high mag — dim)
]


# ===================== HELPER FUNCTIONS =====================
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
        st.error(f"Dosya yuklenirken hata: {e}")
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


def auto_detect_columns(df):
    """Auto-detect RA, Dec, Magnitude, and Name columns."""
    cols = {c.lower(): c for c in df.columns}
    numeric = list(df.select_dtypes(include=[np.number]).columns)

    ra = None
    dec = None
    mag = None
    name = None

    # RA detection
    for pattern in ["ra_j2000", "ra_2000", "ra", "right_ascension", "ra_deg"]:
        if pattern in cols:
            ra = cols[pattern]
            break
    # Dec detection
    for pattern in ["dec_j2000", "dec_2000", "dec", "declination", "dec_deg", "de"]:
        if pattern in cols:
            dec = cols[pattern]
            break
    # Magnitude detection
    for pattern in ["magnitude", "mag", "vmag", "gmag", "phot_g_mean_mag"]:
        if pattern in cols:
            mag = cols[pattern]
            break
    # Name detection
    for pattern in ["star_name", "name", "main_id", "designation", "source_id", "id"]:
        if pattern in cols:
            name = cols[pattern]
            break

    # Fallback: first two numeric columns for RA/Dec
    if ra is None and len(numeric) >= 1:
        ra = numeric[0]
    if dec is None and len(numeric) >= 2:
        dec = numeric[1]
    if mag is None and len(numeric) >= 3:
        mag = numeric[2]
    if name is None:
        name = df.columns[0]

    return {"ra": ra, "dec": dec, "mag": mag, "name": name}


def create_sky_scatter(df, ra_col, dec_col, name_col, mag_col=None, title="Gokyuzu Haritasi"):
    """Create a Plotly sky map scatter plot."""
    hover_data = {name_col: True, ra_col: ":.4f", dec_col: ":.4f"}
    if mag_col:
        hover_data[mag_col] = ":.2f"

    if mag_col and mag_col in df.columns:
        mag_min = df[mag_col].min()
        mag_max = df[mag_col].max()
        mag_range = mag_max - mag_min if mag_max != mag_min else 1
        sizes = ((mag_max - df[mag_col]) / mag_range * 25 + 8).clip(8, 35)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[ra_col],
            y=df[dec_col],
            mode="markers+text",
            marker=dict(
                size=sizes,
                color=df[mag_col],
                colorscale=STAR_COLORSCALE,
                colorbar=dict(title="Mag", tickfont=dict(color="#c0c0d0")),
                line=dict(width=1, color="rgba(255,255,255,0.4)"),
            ),
            text=df[name_col],
            textposition="top center",
            textfont=dict(size=10, color="#f0c040"),
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"RA: %{{x:.4f}}°<br>"
                f"Dec: %{{y:.4f}}°<br>"
                f"Mag: %{{marker.color:.2f}}"
                "<extra></extra>"
            ),
        ))
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[ra_col],
            y=df[dec_col],
            mode="markers+text",
            marker=dict(size=14, color="#4fc3f7", line=dict(width=1, color="white")),
            text=df[name_col],
            textposition="top center",
            textfont=dict(size=10, color="#f0c040"),
            hovertemplate="<b>%{text}</b><br>RA: %{x:.4f}°<br>Dec: %{y:.4f}°<extra></extra>",
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=title,
        xaxis_title="RA (J2000) [derece]",
        yaxis_title="Dec (J2000) [derece]",
        xaxis=dict(
            **PLOTLY_LAYOUT["xaxis"],
            autorange="reversed",
        ),
        height=500,
    )
    return fig


def create_magnitude_bar(df, name_col, mag_col, title="Yildiz Parlakliklari"):
    """Create a Plotly horizontal bar chart for magnitudes."""
    df_sorted = df.sort_values(mag_col, ascending=True)

    fig = go.Figure(go.Bar(
        y=df_sorted[name_col],
        x=df_sorted[mag_col],
        orientation="h",
        marker=dict(
            color=df_sorted[mag_col],
            colorscale=STAR_COLORSCALE,
            line=dict(width=1, color="rgba(255,255,255,0.3)"),
        ),
        hovertemplate="<b>%{y}</b><br>Magnitude: %{x:.2f}<extra></extra>",
    ))

    fig.add_vline(x=0, line_dash="dash", line_color="rgba(240,192,64,0.4)")

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=title,
        xaxis_title="Parlaklik (Magnitude)",
        yaxis_title="",
        height=max(300, len(df) * 45),
    )
    return fig


def create_heatmap(matrix_df, title="Aci Mesafe Matrisi (derece)"):
    """Create a Plotly heatmap from a separation matrix."""
    fig = go.Figure(go.Heatmap(
        z=matrix_df.values,
        x=matrix_df.columns.tolist(),
        y=matrix_df.index.tolist(),
        colorscale="YlOrRd",
        text=matrix_df.round(1).values,
        texttemplate="%{text}",
        textfont=dict(size=11),
        hovertemplate="%{y} ↔ %{x}<br>Mesafe: %{z:.2f}°<extra></extra>",
        colorbar=dict(title="derece", tickfont=dict(color="#c0c0d0")),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=title,
        height=max(400, len(matrix_df) * 55 + 100),
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], tickangle=45),
    )
    return fig


def export_dataframe(df, filename="export.csv"):
    """Provide a CSV download button."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="CSV Olarak Indir",
        data=csv,
        file_name=filename,
        mime="text/csv",
    )


def safe_simbad_query(query_type, **kwargs):
    """SIMBAD query with timeout handling."""
    try:
        from astroquery.simbad import Simbad

        simbad = Simbad()
        simbad.TIMEOUT = 15

        if query_type == "object":
            result = simbad.query_object(kwargs["name"])
        elif query_type == "region":
            center = SkyCoord(
                ra=kwargs["ra"] * u.degree,
                dec=kwargs["dec"] * u.degree,
                frame="icrs",
            )
            result = simbad.query_region(center, radius=kwargs["radius"] * u.degree)
        else:
            return None

        if result is not None:
            return result.to_pandas()
        return None
    except Exception as e:
        st.error(f"SIMBAD sorgu hatasi: {e}")
        return None


def count_data_files(directory):
    """Count non-gitkeep files in a directory."""
    if not directory.exists():
        return 0
    return len([f for f in directory.glob("*") if f.name != ".gitkeep" and f.is_file()])


# ===================== SIDEBAR =====================
st.sidebar.markdown(
    """
    <div style="text-align:center; padding: 10px 0 5px;">
        <span style="font-size: 2.2rem;">⭐</span>
        <h1 style="margin: 4px 0; font-size: 1.6rem; letter-spacing: 2px;">SOFIV2</h1>
        <p style="color: #a0a0b8; font-size: 0.8rem; margin: 0;">Yildiz Katalogu Analiz Araci</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Sayfa",
    [
        "Dashboard",
        "Katalog Goruntüleyici",
        "Gokyuzu Haritasi",
        "Parlaklik Analizi",
        "Cross-Match",
        "SIMBAD Sorgusu",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("v2.0 — Premium Edition")


# ===================== PAGE: DASHBOARD =====================
if page == "Dashboard":
    st.markdown(
        '<h1 style="text-align:center; letter-spacing: 3px;">SOFIV2 DASHBOARD</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center; color:#a0a0b8; margin-top:-10px;">'
        "Tarihi ve modern yildiz kataloglarini analiz et, karsilastir, goruntule</p>",
        unsafe_allow_html=True,
    )

    df = load_template_csv()

    # Metrics row
    st.markdown("")
    m1, m2, m3, m4 = st.columns(4)
    if df is not None:
        m1.metric("Yildiz Sayisi", len(df))
        m2.metric("Katalog Sayisi", df["Catalog"].nunique() if "Catalog" in df.columns else "—")
        m3.metric("Format Sayisi", "3 (CSV/FITS/VOT)")
        avg_mag = df["Magnitude"].mean() if "Magnitude" in df.columns else 0
        m4.metric("Ort. Parlaklik", f"{avg_mag:.2f} mag")
    else:
        m1.metric("Yildiz Sayisi", "—")
        m2.metric("Katalog Sayisi", "—")
        m3.metric("Format Sayisi", "—")
        m4.metric("Ort. Parlaklik", "—")

    st.markdown("---")

    # Two-column layout: sky map + directory status
    col_left, col_right = st.columns([2, 1])

    with col_left:
        if df is not None:
            detected = auto_detect_columns(df)
            if detected["ra"] and detected["dec"] and detected["name"]:
                fig = create_sky_scatter(
                    df,
                    detected["ra"],
                    detected["dec"],
                    detected["name"],
                    detected["mag"],
                    title="Sablon Katalog — Gokyuzu Onizleme",
                )
                fig.update_layout(height=380)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sablon katalog bulunamadi. `python scripts/create_template_fits.py` calistirin.")

    with col_right:
        st.markdown("#### Dizin Durumu")
        dirs_info = [
            ("Historical/", HISTORICAL, "Tarihi kataloglar"),
            ("Modern/", MODERN, "Gaia, SDSS, Pan-STARRS"),
            ("Processed/", PROCESSED, "Islenmus veriler"),
        ]
        for name, path, desc in dirs_info:
            count = count_data_files(path)
            if count > 0:
                st.success(f"**{name}** — {count} dosya")
            else:
                st.markdown(
                    f'<div class="guide-card"><h4>{name}</h4><p>{desc}</p></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("")
        st.markdown("#### Hizli Baslangic")
        st.markdown(
            """
            1. **Katalog Goruntüleyici** ile dosya yukle
            2. **Gokyuzu Haritasi** ile koordinatlari goruntule
            3. **Cross-Match** ile kataloglari eslestir
            4. **SIMBAD** ile online veri cek
            """
        )

    # Template table
    if df is not None:
        with st.expander("Sablon Katalog Tablosu", expanded=False):
            st.dataframe(df, use_container_width=True)


# ===================== PAGE: CATALOG VIEWER =====================
elif page == "Katalog Goruntüleyici":
    st.title("Katalog Goruntüleyici")

    tab1, tab2 = st.tabs(["Dosya Yukle", "Sablon Kataloglar"])

    with tab1:
        uploaded = st.file_uploader(
            "Katalog dosyasi yukle",
            type=["csv", "fits", "fit", "vot", "votable"],
            help="CSV, FITS veya VOTable formatinda dosya yukleyin",
        )
        if uploaded:
            df_uploaded = load_catalog_file(uploaded)
            if df_uploaded is not None:
                st.session_state["uploaded_catalog"] = df_uploaded
                st.success(f"{len(df_uploaded)} satir, {len(df_uploaded.columns)} kolon yuklendi")
                st.dataframe(df_uploaded, use_container_width=True)

                with st.expander("Kolon Istatistikleri"):
                    numeric_cols = df_uploaded.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        st.dataframe(
                            df_uploaded[numeric_cols].describe().round(4),
                            use_container_width=True,
                        )

                export_dataframe(df_uploaded, f"{uploaded.name.rsplit('.', 1)[0]}_export.csv")

    with tab2:
        fmt = st.selectbox("Format", ["CSV", "FITS", "VOTable"])
        df_template = None

        if fmt == "CSV":
            df_template = load_template_csv()
        elif fmt == "FITS":
            path = TEMPLATES / "star_catalog_template.fits"
            if path.exists():
                df_template = load_fits_table(str(path))
            else:
                st.warning("FITS sablonu bulunamadi. `python scripts/create_template_fits.py` calistirin.")
        else:
            path = TEMPLATES / "star_catalog_template.vot"
            if path.exists():
                df_template = load_votable(str(path))
            else:
                st.warning("VOTable sablonu bulunamadi. `python scripts/create_template_fits.py` calistirin.")

        if df_template is not None:
            st.dataframe(df_template, use_container_width=True)

            with st.expander("Kolon Istatistikleri"):
                numeric_cols = df_template.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.dataframe(
                        df_template[numeric_cols].describe().round(4),
                        use_container_width=True,
                    )

            export_dataframe(df_template, f"template_{fmt.lower()}_export.csv")


# ===================== PAGE: SKY MAP =====================
elif page == "Gokyuzu Haritasi":
    st.title("Gokyuzu Haritasi")

    source = st.radio("Veri kaynagi", ["Sablon katalog", "Dosya yukle"], horizontal=True)

    df = None
    if source == "Sablon katalog":
        df = load_template_csv()
    else:
        uploaded = st.file_uploader(
            "Katalog yukle", type=["csv", "fits", "fit", "vot", "votable"]
        )
        if uploaded:
            df = load_catalog_file(uploaded)

    if df is not None:
        detected = auto_detect_columns(df)
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        all_cols = list(df.columns)

        # Column mapping with auto-detect
        col1, col2, col3 = st.columns(3)
        ra_idx = numeric_cols.index(detected["ra"]) if detected["ra"] in numeric_cols else 0
        dec_idx = numeric_cols.index(detected["dec"]) if detected["dec"] in numeric_cols else min(1, len(numeric_cols) - 1)
        name_idx = all_cols.index(detected["name"]) if detected["name"] in all_cols else 0

        ra_col = col1.selectbox("RA kolonu", numeric_cols, index=ra_idx)
        dec_col = col2.selectbox("Dec kolonu", numeric_cols, index=dec_idx)
        name_col = col3.selectbox("Isim kolonu", all_cols, index=name_idx)

        mag_col = None
        if len(numeric_cols) > 2:
            mag_options = ["Yok"] + numeric_cols
            mag_default = mag_options.index(detected["mag"]) if detected["mag"] in mag_options else 0
            mag_col = st.selectbox("Parlaklik kolonu (opsiyonel)", mag_options, index=mag_default)
            if mag_col == "Yok":
                mag_col = None

        # Sky map
        fig = create_sky_scatter(df, ra_col, dec_col, name_col, mag_col)
        st.plotly_chart(fig, use_container_width=True)

        # Galactic coordinates table
        st.markdown("---")
        st.subheader("Galaktik Koordinatlar")
        coords = compute_coords(df, ra_col, dec_col)
        galactic = coords.galactic

        gal_df = pd.DataFrame(
            {
                "Isim": df[name_col],
                "RA (derece)": df[ra_col].round(4),
                "Dec (derece)": df[dec_col].round(4),
                "l (Galaktik Boylam)": [g.l.degree for g in galactic],
                "b (Galaktik Enlem)": [g.b.degree for g in galactic],
            }
        )
        st.dataframe(gal_df.round(4), use_container_width=True)
        export_dataframe(gal_df.round(4), "galactic_coordinates.csv")


# ===================== PAGE: MAGNITUDE ANALYSIS =====================
elif page == "Parlaklik Analizi":
    st.title("Parlaklik Analizi")

    source = st.radio("Veri kaynagi", ["Sablon katalog", "Dosya yukle"], horizontal=True)

    df = None
    if source == "Sablon katalog":
        df = load_template_csv()
    else:
        uploaded = st.file_uploader(
            "Katalog yukle", type=["csv", "fits", "fit", "vot", "votable"]
        )
        if uploaded:
            df = load_catalog_file(uploaded)

    if df is not None:
        detected = auto_detect_columns(df)
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        all_cols = list(df.columns)

        col1, col2 = st.columns(2)
        mag_idx = numeric_cols.index(detected["mag"]) if detected["mag"] in numeric_cols else 0
        name_idx = all_cols.index(detected["name"]) if detected["name"] in all_cols else 0
        mag_col = col1.selectbox("Parlaklik kolonu", numeric_cols, index=mag_idx)
        name_col = col2.selectbox("Isim kolonu", all_cols, index=name_idx)

        # Bar chart
        fig_bar = create_magnitude_bar(df, name_col, mag_col)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Two charts side by side
        chart_left, chart_right = st.columns(2)

        with chart_left:
            # Histogram
            fig_hist = go.Figure(go.Histogram(
                x=df[mag_col],
                nbinsx=15,
                marker=dict(color="#4fc3f7", line=dict(width=1, color="rgba(255,255,255,0.3)")),
                hovertemplate="Aralik: %{x}<br>Sayi: %{y}<extra></extra>",
            ))
            fig_hist.update_layout(
                **PLOTLY_LAYOUT,
                title="Parlaklik Dagilimi",
                xaxis_title="Magnitude",
                yaxis_title="Sayi",
                height=350,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with chart_right:
            # Box plot by catalog if available
            cat_col = None
            for pattern in ["catalog", "catalogue", "source", "survey"]:
                matches = [c for c in df.columns if pattern in c.lower()]
                if matches:
                    cat_col = matches[0]
                    break

            if cat_col and df[cat_col].nunique() > 1:
                fig_box = px.box(
                    df,
                    x=cat_col,
                    y=mag_col,
                    color=cat_col,
                    title="Kataloglara Gore Dagılım",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
            else:
                fig_box = px.box(
                    df,
                    y=mag_col,
                    title="Parlaklik Box Plot",
                    color_discrete_sequence=["#4fc3f7"],
                )
            fig_box.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

        # Stats table
        st.markdown("---")
        st.subheader("Istatistik Ozeti")
        stats = df[mag_col].describe()
        stats_df = pd.DataFrame(
            {
                "Metrik": ["Sayi", "Ortalama", "Std. Sapma", "Min", "Q1 (25%)", "Medyan", "Q3 (75%)", "Max"],
                "Deger": [
                    f"{stats['count']:.0f}",
                    f"{stats['mean']:.4f}",
                    f"{stats['std']:.4f}",
                    f"{stats['min']:.4f}",
                    f"{stats['25%']:.4f}",
                    f"{stats['50%']:.4f}",
                    f"{stats['75%']:.4f}",
                    f"{stats['max']:.4f}",
                ],
            }
        )
        st.dataframe(stats_df, use_container_width=True, hide_index=True)


# ===================== PAGE: CROSS-MATCH =====================
elif page == "Cross-Match":
    st.title("Katalog Cross-Match")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="glass-card"><h3 style="color:#4fc3f7;">Katalog 1</h3></div>',
            unsafe_allow_html=True,
        )
        src1 = st.radio("Kaynak 1", ["Sablon", "Dosya yukle"], key="src1", horizontal=True)
        df1 = None
        if src1 == "Sablon":
            df1 = load_template_csv()
        else:
            up1 = st.file_uploader("Dosya 1", type=["csv", "fits", "fit", "vot"], key="up1")
            if up1:
                df1 = load_catalog_file(up1)
        if df1 is not None:
            st.caption(f"{len(df1)} satir, {len(df1.columns)} kolon")

    with col2:
        st.markdown(
            '<div class="glass-card"><h3 style="color:#4fc3f7;">Katalog 2</h3></div>',
            unsafe_allow_html=True,
        )
        src2 = st.radio("Kaynak 2", ["Sablon", "Dosya yukle"], key="src2", horizontal=True)
        df2 = None
        if src2 == "Sablon":
            df2 = load_template_csv()
        else:
            up2 = st.file_uploader("Dosya 2", type=["csv", "fits", "fit", "vot"], key="up2")
            if up2:
                df2 = load_catalog_file(up2)
        if df2 is not None:
            st.caption(f"{len(df2)} satir, {len(df2.columns)} kolon")

    if df1 is not None and df2 is not None:
        st.markdown("---")

        # Column mapping
        det1 = auto_detect_columns(df1)
        det2 = auto_detect_columns(df2)
        num1 = list(df1.select_dtypes(include=[np.number]).columns)
        num2 = list(df2.select_dtypes(include=[np.number]).columns)
        all1 = list(df1.columns)
        all2 = list(df2.columns)

        c1, c2, c3, c4 = st.columns(4)
        ra1 = c1.selectbox("RA 1", num1, index=num1.index(det1["ra"]) if det1["ra"] in num1 else 0)
        dec1 = c2.selectbox("Dec 1", num1, index=num1.index(det1["dec"]) if det1["dec"] in num1 else min(1, len(num1) - 1))
        ra2 = c3.selectbox("RA 2", num2, index=num2.index(det2["ra"]) if det2["ra"] in num2 else 0)
        dec2 = c4.selectbox("Dec 2", num2, index=num2.index(det2["dec"]) if det2["dec"] in num2 else min(1, len(num2) - 1))

        cn1, cn2 = st.columns(2)
        name1_col = cn1.selectbox(
            "Isim kolonu (Katalog 1)",
            all1,
            index=all1.index(det1["name"]) if det1["name"] in all1 else 0,
        )
        name2_col = cn2.selectbox(
            "Isim kolonu (Katalog 2)",
            all2,
            index=all2.index(det2["name"]) if det2["name"] in all2 else 0,
        )

        # Separation matrix for catalog 1
        coords1 = compute_coords(df1, ra1, dec1)
        names1 = df1[name1_col].astype(str).tolist()
        sep_df = compute_separation_matrix(coords1, names1)

        st.subheader("Aci Mesafe Matrisi (Katalog 1)")
        fig_heat = create_heatmap(sep_df)
        st.plotly_chart(fig_heat, use_container_width=True)

        # Cross-match
        st.markdown("---")
        st.subheader("Cross-Match Sonuclari")
        threshold = st.slider("Eslesme esigi (arcsec)", 1.0, 60.0, 5.0, 0.5)

        coords2 = compute_coords(df2, ra2, dec2)
        names2 = df2[name2_col].astype(str).tolist()
        idx, sep2d, _ = coords1.match_to_catalog_sky(coords2)

        matches = []
        for i in range(len(coords1)):
            sep_arcsec = sep2d[i].arcsecond
            if sep_arcsec <= threshold:
                matches.append(
                    {
                        "Katalog 1": names1[i],
                        "Katalog 2": names2[idx[i]],
                        "Mesafe (arcsec)": round(sep_arcsec, 3),
                        "RA_1": df1[ra1].iloc[i],
                        "Dec_1": df1[dec1].iloc[i],
                        "RA_2": df2[ra2].iloc[idx[i]],
                        "Dec_2": df2[dec2].iloc[idx[i]],
                    }
                )

        if matches:
            match_df = pd.DataFrame(matches)
            st.success(f"{len(matches)} eslesme bulundu ({threshold}\" esik)")
            st.dataframe(
                match_df[["Katalog 1", "Katalog 2", "Mesafe (arcsec)"]],
                use_container_width=True,
            )
            export_dataframe(match_df, "cross_match_results.csv")

            # Sky map with match lines
            fig_match = go.Figure()

            # Draw connection lines
            for m in matches:
                fig_match.add_trace(go.Scatter(
                    x=[m["RA_1"], m["RA_2"]],
                    y=[m["Dec_1"], m["Dec_2"]],
                    mode="lines",
                    line=dict(color="rgba(240,192,64,0.4)", width=1, dash="dot"),
                    showlegend=False,
                    hoverinfo="skip",
                ))

            # Catalog 1 points
            fig_match.add_trace(go.Scatter(
                x=df1[ra1],
                y=df1[dec1],
                mode="markers+text",
                marker=dict(size=12, color="#4fc3f7", symbol="circle", line=dict(width=1, color="white")),
                text=names1,
                textposition="top center",
                textfont=dict(size=9, color="#4fc3f7"),
                name="Katalog 1",
                hovertemplate="<b>%{text}</b> (K1)<br>RA: %{x:.4f}<br>Dec: %{y:.4f}<extra></extra>",
            ))

            # Catalog 2 points
            fig_match.add_trace(go.Scatter(
                x=df2[ra2],
                y=df2[dec2],
                mode="markers+text",
                marker=dict(size=12, color="#f0c040", symbol="diamond", line=dict(width=1, color="white")),
                text=names2,
                textposition="bottom center",
                textfont=dict(size=9, color="#f0c040"),
                name="Katalog 2",
                hovertemplate="<b>%{text}</b> (K2)<br>RA: %{x:.4f}<br>Dec: %{y:.4f}<extra></extra>",
            ))

            fig_match.update_layout(
                **PLOTLY_LAYOUT,
                title="Cross-Match Gokyuzu Haritasi",
                xaxis_title="RA [derece]",
                yaxis_title="Dec [derece]",
                xaxis=dict(**PLOTLY_LAYOUT["xaxis"], autorange="reversed"),
                height=500,
            )
            st.plotly_chart(fig_match, use_container_width=True)
        else:
            st.warning(f"{threshold}\" esik degerinde eslesme bulunamadi.")


# ===================== PAGE: SIMBAD QUERY =====================
elif page == "SIMBAD Sorgusu":
    st.title("SIMBAD Sorgusu")
    st.caption("Astronomik veritabanindan yildiz bilgisi cek (internet gerektirir)")

    query_type = st.radio("Sorgu tipi", ["Isimle Ara", "Bolge Aramasi (Cone Search)"], horizontal=True)

    if query_type == "Isimle Ara":
        star_name = st.text_input("Yildiz adi", value="Sirius")
        if st.button("Sorgula", type="primary") and star_name:
            with st.spinner("SIMBAD sorgulanıyor..."):
                result_df = safe_simbad_query("object", name=star_name)
                if result_df is not None:
                    st.session_state["last_simbad"] = result_df
                    st.success(f"'{star_name}' bulundu!")
                    st.dataframe(result_df, use_container_width=True)
                    export_dataframe(result_df, f"simbad_{star_name}.csv")
                else:
                    st.warning(f"'{star_name}' bulunamadi veya baglanti hatasi.")

    else:
        col1, col2, col3 = st.columns(3)
        ra_input = col1.number_input("RA (derece)", value=101.2871, format="%.4f")
        dec_input = col2.number_input("Dec (derece)", value=-16.7161, format="%.4f")
        radius = col3.number_input(
            "Yaricap (derece)", value=0.1, min_value=0.01, max_value=5.0, format="%.2f"
        )

        if st.button("Bolge Sorgula", type="primary"):
            with st.spinner("SIMBAD sorgulanıyor..."):
                result_df = safe_simbad_query(
                    "region", ra=ra_input, dec=dec_input, radius=radius
                )
                if result_df is not None:
                    st.session_state["last_simbad"] = result_df
                    st.success(f"{len(result_df)} nesne bulundu ({radius} derece yaricap)")
                    st.dataframe(result_df, use_container_width=True)
                    export_dataframe(result_df, "simbad_cone_search.csv")

                    # Sky plot of results
                    ra_col_name = None
                    dec_col_name = None
                    for c in result_df.columns:
                        cl = c.lower()
                        if "ra" in cl and ra_col_name is None:
                            ra_col_name = c
                        if "dec" in cl and dec_col_name is None:
                            dec_col_name = c

                    if ra_col_name and dec_col_name:
                        result_numeric = result_df[[ra_col_name, dec_col_name]].apply(
                            pd.to_numeric, errors="coerce"
                        )
                        valid = result_numeric.dropna()
                        if len(valid) > 0:
                            fig_simbad = go.Figure()
                            fig_simbad.add_trace(go.Scatter(
                                x=valid[ra_col_name],
                                y=valid[dec_col_name],
                                mode="markers",
                                marker=dict(size=6, color="#4fc3f7", opacity=0.7),
                                hovertemplate="RA: %{x:.4f}<br>Dec: %{y:.4f}<extra></extra>",
                            ))
                            # Search center
                            fig_simbad.add_trace(go.Scatter(
                                x=[ra_input],
                                y=[dec_input],
                                mode="markers",
                                marker=dict(
                                    size=14, color="#f0c040", symbol="x",
                                    line=dict(width=2, color="#f0c040"),
                                ),
                                name="Arama merkezi",
                                hovertemplate="Merkez<br>RA: %{x:.4f}<br>Dec: %{y:.4f}<extra></extra>",
                            ))
                            fig_simbad.update_layout(
                                **PLOTLY_LAYOUT,
                                title="SIMBAD Sonuclari — Gokyuzu Haritasi",
                                xaxis_title="RA [derece]",
                                yaxis_title="Dec [derece]",
                                xaxis=dict(**PLOTLY_LAYOUT["xaxis"], autorange="reversed"),
                                height=400,
                            )
                            st.plotly_chart(fig_simbad, use_container_width=True)
                else:
                    st.warning("Sonuc bulunamadi veya baglanti hatasi.")

    # Show last SIMBAD result if exists
    if "last_simbad" in st.session_state and st.session_state["last_simbad"] is not None:
        with st.expander("Son SIMBAD Sorgu Sonucu"):
            st.dataframe(st.session_state["last_simbad"], use_container_width=True)
