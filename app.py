"""
Sofiv2 - Star Catalog Analysis Dashboard
=========================================
Built with Dash + Plotly. Run:
    python app.py
Then open http://localhost:8050
"""
import base64
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback, no_update
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
HISTORICAL = ROOT / "Historical"
MODERN = ROOT / "Modern"
PROCESSED = ROOT / "Processed"

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Sofiv2 — Star Catalog Analysis"


# ═══════════════════════════════════════════════════════════
#  DATA HELPERS
# ═══════════════════════════════════════════════════════════
def load_template_csv():
    path = TEMPLATES / "star_catalog_template.csv"
    return pd.read_csv(path) if path.exists() else None


def load_fits_table(filepath):
    try:
        return Table.read(str(filepath), format="fits").to_pandas()
    except Exception:
        return None


def load_votable(filepath):
    try:
        return Table.read(str(filepath), format="votable").to_pandas()
    except Exception:
        return None


def parse_upload(contents, filename):
    """Parse uploaded file from Dash dcc.Upload."""
    if contents is None:
        return None
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    name = filename.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif name.endswith((".fits", ".fit")):
            return Table.read(io.BytesIO(decoded), format="fits").to_pandas()
        elif name.endswith((".vot", ".votable", ".xml")):
            return Table.read(io.BytesIO(decoded), format="votable").to_pandas()
    except Exception:
        return None
    return None


def compute_coords(df, ra_col, dec_col):
    return SkyCoord(
        ra=df[ra_col].values * u.degree,
        dec=df[dec_col].values * u.degree,
        frame="icrs",
    )


def compute_separation_matrix(coords, names):
    n = len(coords)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            sep = coords[i].separation(coords[j]).degree
            matrix[i][j] = sep
            matrix[j][i] = sep
    return pd.DataFrame(matrix, index=names, columns=names)


def auto_detect(df):
    cols = {c.lower(): c for c in df.columns}
    numeric = list(df.select_dtypes(include=[np.number]).columns)
    r = {"ra": None, "dec": None, "mag": None, "name": None}
    for p in ["ra_j2000", "ra_2000", "ra", "right_ascension"]:
        if p in cols: r["ra"] = cols[p]; break
    for p in ["dec_j2000", "dec_2000", "dec", "declination"]:
        if p in cols: r["dec"] = cols[p]; break
    for p in ["magnitude", "mag", "vmag", "gmag"]:
        if p in cols: r["mag"] = cols[p]; break
    for p in ["star_name", "name", "main_id", "designation"]:
        if p in cols: r["name"] = cols[p]; break
    if r["ra"] is None and len(numeric) >= 1: r["ra"] = numeric[0]
    if r["dec"] is None and len(numeric) >= 2: r["dec"] = numeric[1]
    if r["mag"] is None and len(numeric) >= 3: r["mag"] = numeric[2]
    if r["name"] is None: r["name"] = df.columns[0]
    return r


def count_files(directory):
    if not directory.exists():
        return 0
    return len([f for f in directory.glob("*") if f.name != ".gitkeep" and f.is_file()])


def safe_simbad(qtype, **kw):
    try:
        from astroquery.simbad import Simbad
        s = Simbad()
        s.TIMEOUT = 15
        if qtype == "object":
            res = s.query_object(kw["name"])
        elif qtype == "region":
            c = SkyCoord(ra=kw["ra"] * u.degree, dec=kw["dec"] * u.degree, frame="icrs")
            res = s.query_region(c, radius=kw["radius"] * u.degree)
        else:
            return None
        return res.to_pandas() if res is not None else None
    except Exception as e:
        return str(e)


# ═══════════════════════════════════════════════════════════
#  PLOTLY THEME
# ═══════════════════════════════════════════════════════════
ACCENT = "#818cf8"
COLORS = [[0, "#ef4444"], [0.25, "#f97316"], [0.45, "#eab308"], [0.65, "#38bdf8"], [1, "#3b82f6"]]


def playout(**kw):
    """Build Plotly layout dict with dark theme."""
    ax_defaults = dict(
        gridcolor="rgba(30,32,53,0.8)",
        zerolinecolor="#1e2035",
        tickfont=dict(color="#6b7280"),
        title_font=dict(color="#9ca3af"),
    )
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(16,17,26,0.6)",
        font=dict(color="#9ca3af", family="Inter, sans-serif", size=12),
        title_font=dict(color="#e2e4ea", size=15),
        legend=dict(bgcolor="rgba(16,17,26,0.8)", bordercolor="#1e2035", borderwidth=1),
        margin=dict(l=50, r=20, t=50, b=50),
        hoverlabel=dict(bgcolor="#1e2035", bordercolor="#313456", font=dict(color="#f0f1f5")),
    )
    base["xaxis"] = {**ax_defaults, **kw.pop("xaxis", {})}
    base["yaxis"] = {**ax_defaults, **kw.pop("yaxis", {})}
    base.update(kw)
    return base


def make_sky_chart(df, ra, dec, name, mag=None, title="Sky Map", height=460):
    fig = go.Figure()
    if mag and mag in df.columns:
        mn, mx = df[mag].min(), df[mag].max()
        rng = mx - mn if mx != mn else 1
        sizes = ((mx - df[mag]) / rng * 28 + 8).clip(8, 38)
        fig.add_trace(go.Scatter(
            x=df[ra], y=df[dec], mode="markers+text",
            marker=dict(size=sizes, color=df[mag], colorscale=COLORS,
                        colorbar=dict(title="Mag", tickfont=dict(color="#6b7280"), thickness=12, len=0.6),
                        line=dict(width=0.8, color="rgba(255,255,255,0.2)")),
            text=df[name], textposition="top center",
            textfont=dict(size=10, color="#c8ccd4"),
            hovertemplate="<b>%{text}</b><br>RA: %{x:.4f}°<br>Dec: %{y:.4f}°<br>Mag: %{marker.color:.2f}<extra></extra>",
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df[ra], y=df[dec], mode="markers+text",
            marker=dict(size=12, color=ACCENT, line=dict(width=1, color="#fff")),
            text=df[name], textposition="top center",
            textfont=dict(size=10, color="#c8ccd4"),
            hovertemplate="<b>%{text}</b><br>RA: %{x:.4f}°<br>Dec: %{y:.4f}°<extra></extra>",
        ))
    fig.update_layout(**playout(
        title=title,
        xaxis=dict(title="RA (J2000) [deg]", autorange="reversed"),
        yaxis=dict(title="Dec (J2000) [deg]"),
        height=height, showlegend=False,
    ))
    return fig


def make_data_table(df, page_size=15):
    display = df.copy()
    for col in display.select_dtypes(include=[np.number]).columns:
        display[col] = display[col].round(4)
    return dash_table.DataTable(
        data=display.to_dict("records"),
        columns=[{"name": c, "id": c} for c in display.columns],
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        style_as_list_view=True,
        style_table={"borderRadius": "10px", "overflow": "hidden", "border": "1px solid #e5e7eb"},
        style_header={
            "backgroundColor": "#f8fafc",
            "color": "#475569",
            "fontWeight": "600",
            "fontSize": "0.72rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "borderBottom": "2px solid #e2e8f0",
            "fontFamily": "Inter, sans-serif",
            "padding": "10px 14px",
        },
        style_cell={
            "backgroundColor": "#ffffff",
            "color": "#1e293b",
            "borderColor": "#f1f5f9",
            "fontFamily": "JetBrains Mono, monospace",
            "fontSize": "0.8rem",
            "padding": "9px 14px",
            "textAlign": "left",
            "maxWidth": "200px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
            {"if": {"state": "active"}, "backgroundColor": "#eef2ff", "border": "1px solid #818cf8"},
        ],
        style_filter={
            "backgroundColor": "#f8fafc",
            "color": "#1e293b",
            "borderColor": "#e2e8f0",
            "fontFamily": "Inter, sans-serif",
            "fontSize": "0.8rem",
        },
    )


# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
NAV_ITEMS = [
    ("dashboard", "Dashboard", "📊"),
    ("catalog", "Catalog Viewer", "📋"),
    ("skymap", "Sky Map", "🗺️"),
    ("magnitude", "Magnitude Analysis", "💡"),
    ("crossmatch", "Cross-Match", "🔗"),
    ("simbad", "SIMBAD Query", "🔭"),
]


def make_sidebar():
    return html.Nav(className="sidebar", children=[
        html.Div(className="sidebar-logo", children=[
            html.Div("🌌", className="icon"),
            html.H1("SOFIV2"),
            html.P("Star Catalog Analysis"),
        ]),
        html.Div(className="sidebar-nav", children=[
            html.Div("Navigation", className="nav-label"),
            *[
                html.Div(
                    id={"type": "nav-item", "index": key},
                    className="nav-item",
                    children=[html.Span(icon, className="nav-icon"), label],
                    n_clicks=0,
                )
                for key, label, icon in NAV_ITEMS
            ],
        ]),
        html.Div(className="sidebar-footer", children=[
            html.P("v2.0 DASH EDITION"),
        ]),
    ])


# ═══════════════════════════════════════════════════════════
#  PAGES
# ═══════════════════════════════════════════════════════════
def page_dashboard():
    df = load_template_csv()
    n_stars = len(df) if df is not None else 0
    n_cats = df["Catalog"].nunique() if df is not None and "Catalog" in df.columns else 0
    avg_mag = df["Magnitude"].mean() if df is not None and "Magnitude" in df.columns else 0

    sky_chart = html.Div()
    if df is not None:
        det = auto_detect(df)
        if det["ra"] and det["dec"] and det["name"]:
            fig = make_sky_chart(df, det["ra"], det["dec"], det["name"], det["mag"],
                                title="Template Catalog Preview", height=360)
            sky_chart = dcc.Graph(figure=fig, config={"displayModeBar": True, "displaylogo": False})

    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("Dashboard"),
            html.P("Yildiz katalog verilerine genel bakis"),
        ]),
        # Stats
        html.Div(className="stat-grid", children=[
            html.Div(className="stat-card", children=[
                html.Div("Yildiz Sayisi", className="stat-label"),
                html.Div(str(n_stars), className="stat-value"),
                html.Div("template catalog", className="stat-sub"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Katalog Sayisi", className="stat-label"),
                html.Div(str(n_cats), className="stat-value"),
                html.Div("unique sources", className="stat-sub"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Desteklenen Format", className="stat-label"),
                html.Div("3", className="stat-value"),
                html.Div("CSV · FITS · VOTable", className="stat-sub"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Ort. Parlaklik", className="stat-label"),
                html.Div(f"{avg_mag:.2f}", className="stat-value"),
                html.Div("magnitude (V/G)", className="stat-sub"),
            ]),
        ]),
        # Chart + Sidebar
        html.Div(className="grid-5-3", children=[
            html.Div(className="section-card", children=[
                html.H3("Gokyuzu Onizleme"),
                sky_chart,
            ]),
            html.Div(children=[
                html.Div(className="section-card", children=[
                    html.H3("Dizin Durumu"),
                    *[
                        html.Div(className="dir-item", children=[
                            html.Div(children=[
                                html.Div(name, className="dir-name"),
                                html.Div(desc, className="dir-desc"),
                            ]),
                            html.Span(
                                f"{count_files(path)} dosya" if count_files(path) > 0 else "bos",
                                className=f"badge {'badge-green' if count_files(path) > 0 else 'badge-default'}",
                            ),
                        ])
                        for name, path, desc in [
                            ("Historical/", HISTORICAL, "Tarihi kataloglar"),
                            ("Modern/", MODERN, "Gaia, SDSS, Pan-STARRS"),
                            ("Processed/", PROCESSED, "Islenmus veriler"),
                        ]
                    ],
                ]),
                html.Div(className="section-card", children=[
                    html.H3("Hizli Baslangic"),
                    html.Ul(className="quick-list", children=[
                        html.Li([html.Span("1", className="step-num"), html.Strong("Catalog Viewer"), " — dosya yukle"]),
                        html.Li([html.Span("2", className="step-num"), html.Strong("Sky Map"), " — koordinatlari gor"]),
                        html.Li([html.Span("3", className="step-num"), html.Strong("Cross-Match"), " — kataloglari eslestir"]),
                        html.Li([html.Span("4", className="step-num"), html.Strong("SIMBAD"), " — online veri cek"]),
                    ]),
                ]),
            ]),
        ]),
    ])


def page_catalog():
    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("Catalog Viewer"),
            html.P("CSV, FITS ve VOTable dosyalarini yukle ve incele"),
        ]),
        html.Div(className="tab-bar", children=[
            html.Button("Dosya Yukle", id="cat-tab-upload", className="tab-item active", n_clicks=0),
            html.Button("Sablon Kataloglar", id="cat-tab-template", className="tab-item", n_clicks=0),
        ]),
        html.Div(id="cat-tab-content", children=[
            # Initial content: upload tab
            html.Div(className="section-card", children=[
                dcc.Upload(
                    id="catalog-upload",
                    children=html.Div(className="upload-area", children=[
                        html.Div("📁", className="upload-icon"),
                        html.P(["Dosyayi surukle veya ", html.A("sec")]),
                        html.P("CSV, FITS, VOTable", style={"fontSize": "0.75rem", "color": "#4b5563"}),
                    ]),
                    multiple=False,
                ),
                html.Div(id="catalog-upload-result"),
            ]),
        ]),
    ])


def page_skymap():
    df = load_template_csv()
    det = auto_detect(df) if df is not None else {}
    numeric = list(df.select_dtypes(include=[np.number]).columns) if df is not None else []

    chart = html.Div()
    gal_table = html.Div()
    if df is not None and det.get("ra") and det.get("dec") and det.get("name"):
        fig = make_sky_chart(df, det["ra"], det["dec"], det["name"], det.get("mag"))
        chart = dcc.Graph(figure=fig, config={"displayModeBar": True, "displaylogo": False})

        coords = compute_coords(df, det["ra"], det["dec"])
        gal = coords.galactic
        gal_df = pd.DataFrame({
            "Name": df[det["name"]],
            "RA (deg)": df[det["ra"]].round(4),
            "Dec (deg)": df[det["dec"]].round(4),
            "l (Gal Lon)": [g.l.degree for g in gal],
            "b (Gal Lat)": [g.b.degree for g in gal],
        })
        gal_table = html.Div([
            html.H3("Galaktik Koordinatlar", style={"marginTop": "24px", "marginBottom": "12px"}),
            make_data_table(gal_df),
        ])

    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("Sky Map"),
            html.P("Yildizlari RA/Dec koordinatlarinda interaktif haritada goruntule"),
        ]),
        html.Div(className="section-card", children=[chart]),
        gal_table,
    ])


def page_magnitude():
    df = load_template_csv()
    if df is None:
        return html.Div([
            html.Div(className="page-header", children=[html.H1("Magnitude Analysis"), html.P("Parlaklik analizi")]),
            html.Div("Sablon katalog bulunamadi.", className="alert alert-warning"),
        ])

    det = auto_detect(df)
    mag_col = det["mag"] or list(df.select_dtypes(include=[np.number]).columns)[0]
    name_col = det["name"] or df.columns[0]

    # Bar chart
    df_s = df.sort_values(mag_col, ascending=True)
    fig_bar = go.Figure(go.Bar(
        y=df_s[name_col], x=df_s[mag_col], orientation="h",
        marker=dict(color=df_s[mag_col], colorscale=COLORS, line=dict(width=0), cornerradius=4),
        hovertemplate="<b>%{y}</b><br>Mag: %{x:.2f}<extra></extra>",
    ))
    fig_bar.add_vline(x=0, line_dash="dot", line_color="#2d3052")
    fig_bar.update_layout(**playout(title="Star Magnitudes", xaxis=dict(title="Magnitude"),
                                     height=max(260, len(df) * 48), showlegend=False))

    # Histogram
    fig_hist = go.Figure(go.Histogram(
        x=df[mag_col], nbinsx=15,
        marker=dict(color=ACCENT, line=dict(width=0), cornerradius=3),
    ))
    fig_hist.update_layout(**playout(title="Distribution", xaxis=dict(title="Magnitude"),
                                      yaxis=dict(title="Count"), height=300, showlegend=False))

    # Box plot
    fig_box = go.Figure()
    cat_col = None
    for p in ["catalog", "catalogue", "source"]:
        found = [c for c in df.columns if p in c.lower()]
        if found: cat_col = found[0]; break

    if cat_col and df[cat_col].nunique() > 1:
        for i, cat in enumerate(df[cat_col].unique()):
            sub = df[df[cat_col] == cat]
            fig_box.add_trace(go.Box(
                y=sub[mag_col], name=str(cat),
                marker_color=[ACCENT, "#f97316", "#10b981", "#eab308", "#ef4444"][i % 5],
            ))
    else:
        fig_box.add_trace(go.Box(y=df[mag_col], name="All", marker_color=ACCENT))
    fig_box.update_layout(**playout(title="Box Plot", yaxis=dict(title="Magnitude"),
                                     height=300, showlegend=False))

    # Stats
    s = df[mag_col].describe()

    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("Magnitude Analysis"),
            html.P("Parlaklik dagilimi, histogram ve istatistiksel analiz"),
        ]),
        html.Div(className="section-card", children=[
            dcc.Graph(figure=fig_bar, config={"displaylogo": False}),
        ]),
        html.Div(className="grid-2", children=[
            html.Div(className="section-card", children=[
                dcc.Graph(figure=fig_hist, config={"displaylogo": False}),
            ]),
            html.Div(className="section-card", children=[
                dcc.Graph(figure=fig_box, config={"displaylogo": False}),
            ]),
        ]),
        html.Div(className="stat-grid", style={"marginTop": "16px"}, children=[
            html.Div(className="stat-card", children=[
                html.Div("Min", className="stat-label"),
                html.Div(f"{s['min']:.3f}", className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Ortalama", className="stat-label"),
                html.Div(f"{s['mean']:.3f}", className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Medyan", className="stat-label"),
                html.Div(f"{s['50%']:.3f}", className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("Max", className="stat-label"),
                html.Div(f"{s['max']:.3f}", className="stat-value"),
            ]),
        ]),
    ])


def page_crossmatch():
    df = load_template_csv()
    if df is None:
        return html.Div([
            html.Div(className="page-header", children=[html.H1("Cross-Match")]),
            html.Div("Sablon katalog bulunamadi.", className="alert alert-warning"),
        ])

    det = auto_detect(df)
    ra_col, dec_col = det["ra"], det["dec"]
    name_col = det["name"]

    coords = compute_coords(df, ra_col, dec_col)
    names = df[name_col].astype(str).tolist()
    sep_df = compute_separation_matrix(coords, names)

    # Heatmap
    fig_heat = go.Figure(go.Heatmap(
        z=sep_df.values, x=sep_df.columns.tolist(), y=sep_df.index.tolist(),
        colorscale=[[0, "#10111a"], [0.5, "#6366f1"], [1, "#f97316"]],
        text=sep_df.round(1).values, texttemplate="%{text}",
        textfont=dict(size=11, color="#c8ccd4"),
        hovertemplate="%{y} — %{x}<br>%{z:.2f}°<extra></extra>",
        colorbar=dict(title="deg", tickfont=dict(color="#6b7280"), thickness=12),
    ))
    fig_heat.update_layout(**playout(
        title="Angular Separation Matrix",
        xaxis=dict(tickangle=45),
        height=max(380, len(sep_df) * 55 + 80),
    ))

    # Self cross-match
    idx, sep2d, _ = coords.match_to_catalog_sky(coords)
    matches = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            sep_as = coords[i].separation(coords[j]).arcsecond
            matches.append({
                "Star A": names[i],
                "Star B": names[j],
                "Sep (arcsec)": round(sep_as, 3),
                "Sep (deg)": round(sep_as / 3600, 4),
            })
    match_df = pd.DataFrame(matches).sort_values("Sep (arcsec)")

    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("Cross-Match"),
            html.P("Katalog ici aci mesafe analizi — dosya yukleme icin Catalog Viewer kullanin"),
        ]),
        html.Div(className="section-card", children=[
            dcc.Graph(figure=fig_heat, config={"displaylogo": False}),
        ]),
        html.Div(className="section-card", style={"marginTop": "16px"}, children=[
            html.H3("Tum Yildiz Cifti Mesafeleri"),
            make_data_table(match_df, page_size=10),
        ]),
    ])


def page_simbad():
    return html.Div([
        html.Div(className="page-header", children=[
            html.H1("SIMBAD Query"),
            html.P("Astronomik veritabanindan yildiz bilgisi cek — internet gerektirir"),
        ]),
        html.Div(className="tab-bar", children=[
            html.Button("Isimle Ara", id="sim-tab-name", className="tab-item active", n_clicks=0),
            html.Button("Bolge Aramasi", id="sim-tab-region", className="tab-item", n_clicks=0),
        ]),
        html.Div(id="simbad-form", children=[
            # Initial content: name search
            html.Div(className="section-card", children=[
                html.Div(className="form-row", children=[
                    html.Div(className="form-group", children=[
                        html.Label("Yildiz Adi"),
                        dcc.Input(id="simbad-name", type="text", value="Sirius",
                                  style={"width": "100%"}),
                    ]),
                    html.Div(style={"paddingBottom": "2px"}, children=[
                        html.Button("Sorgula", id="simbad-search-btn",
                                    className="btn btn-primary", n_clicks=0),
                    ]),
                ]),
            ]),
        ]),
        html.Div(id="simbad-result"),
    ])


# ═══════════════════════════════════════════════════════════
#  APP LAYOUT
# ═══════════════════════════════════════════════════════════
app.layout = html.Div(className="app-container", children=[
    dcc.Store(id="current-page", data="dashboard"),
    dcc.Store(id="cat-active-tab", data="upload"),
    dcc.Store(id="sim-active-tab", data="name"),
    make_sidebar(),
    html.Main(className="main-content", id="page-content", children=[
        page_dashboard(),
    ]),
])


# ═══════════════════════════════════════════════════════════
#  CALLBACKS
# ═══════════════════════════════════════════════════════════

# Navigation
@callback(
    Output("page-content", "children"),
    Output("current-page", "data"),
    [Input({"type": "nav-item", "index": key}, "n_clicks") for key, _, _ in NAV_ITEMS],
    State("current-page", "data"),
    prevent_initial_call=True,
)
def navigate(*args):
    clicks = args[:-1]
    current = args[-1]
    from dash import ctx
    if not ctx.triggered_id:
        return no_update, no_update
    page_key = ctx.triggered_id["index"]
    pages = {
        "dashboard": page_dashboard,
        "catalog": page_catalog,
        "skymap": page_skymap,
        "magnitude": page_magnitude,
        "crossmatch": page_crossmatch,
        "simbad": page_simbad,
    }
    return pages.get(page_key, page_dashboard)(), page_key


# Update sidebar active state
@callback(
    [Output({"type": "nav-item", "index": key}, "className") for key, _, _ in NAV_ITEMS],
    Input("current-page", "data"),
)
def update_nav_active(current):
    return [
        "nav-item active" if key == current else "nav-item"
        for key, _, _ in NAV_ITEMS
    ]


# Catalog tab switching
@callback(
    Output("cat-tab-content", "children"),
    Output("cat-tab-upload", "className"),
    Output("cat-tab-template", "className"),
    Output("cat-active-tab", "data"),
    Input("cat-tab-upload", "n_clicks"),
    Input("cat-tab-template", "n_clicks"),
    State("cat-active-tab", "data"),
    prevent_initial_call=True,
)
def switch_catalog_tab(n_upload, n_template, current):
    from dash import ctx
    active = "upload"
    if ctx.triggered_id == "cat-tab-template":
        active = "template"

    if active == "upload":
        content = html.Div(className="section-card", children=[
            dcc.Upload(
                id="catalog-upload",
                children=html.Div(className="upload-area", children=[
                    html.Div("📁", className="upload-icon"),
                    html.P(["Dosyayi surukle veya ", html.A("sec")]),
                    html.P("CSV, FITS, VOTable", style={"fontSize": "0.75rem", "color": "#4b5563"}),
                ]),
                multiple=False,
            ),
            html.Div(id="catalog-upload-result"),
        ])
    else:
        df = load_template_csv()
        if df is not None:
            content = html.Div(className="section-card", children=[
                html.Div(className="alert alert-info", children=[
                    f"Sablon katalog: {len(df)} yildiz, {len(df.columns)} kolon"
                ]),
                make_data_table(df),
            ])
        else:
            content = html.Div(className="alert alert-warning", children=["Sablon bulunamadi."])

    return (
        content,
        "tab-item active" if active == "upload" else "tab-item",
        "tab-item active" if active == "template" else "tab-item",
        active,
    )


# Catalog file upload
@callback(
    Output("catalog-upload-result", "children"),
    Input("catalog-upload", "contents"),
    State("catalog-upload", "filename"),
    prevent_initial_call=True,
)
def handle_catalog_upload(contents, filename):
    if contents is None:
        return no_update
    df = parse_upload(contents, filename)
    if df is None:
        return html.Div(className="alert alert-error", children=["Dosya okunamadi."])
    return html.Div([
        html.Div(className="alert alert-success", children=[
            f"{filename}: {len(df)} satir, {len(df.columns)} kolon"
        ]),
        make_data_table(df),
    ])


# SIMBAD tab switching
@callback(
    Output("simbad-form", "children"),
    Output("sim-tab-name", "className"),
    Output("sim-tab-region", "className"),
    Output("sim-active-tab", "data"),
    Input("sim-tab-name", "n_clicks"),
    Input("sim-tab-region", "n_clicks"),
    State("sim-active-tab", "data"),
    prevent_initial_call=True,
)
def switch_simbad_tab(n_name, n_region, current):
    from dash import ctx
    active = "name"
    if ctx.triggered_id == "sim-tab-region":
        active = "region"

    if active == "name":
        form = html.Div(className="section-card", children=[
            html.Div(className="form-row", children=[
                html.Div(className="form-group", children=[
                    html.Label("Yildiz Adi"),
                    dcc.Input(id="simbad-name", type="text", value="Sirius",
                              style={"width": "100%"}),
                ]),
                html.Div(style={"paddingBottom": "2px"}, children=[
                    html.Button("Sorgula", id="simbad-search-btn", className="btn btn-primary", n_clicks=0),
                ]),
            ]),
        ])
    else:
        form = html.Div(className="section-card", children=[
            html.Div(className="form-row", children=[
                html.Div(className="form-group", children=[
                    html.Label("RA (deg)"),
                    dcc.Input(id="simbad-ra", type="number", value=101.2871, step=0.0001),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Dec (deg)"),
                    dcc.Input(id="simbad-dec", type="number", value=-16.7161, step=0.0001),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Radius (deg)"),
                    dcc.Input(id="simbad-radius", type="number", value=0.1, step=0.01, min=0.01, max=5.0),
                ]),
                html.Div(style={"paddingBottom": "2px"}, children=[
                    html.Button("Sorgula", id="simbad-region-btn", className="btn btn-primary", n_clicks=0),
                ]),
            ]),
        ])

    return (
        form,
        "tab-item active" if active == "name" else "tab-item",
        "tab-item active" if active == "region" else "tab-item",
        active,
    )


# SIMBAD name search
@callback(
    Output("simbad-result", "children", allow_duplicate=True),
    Input("simbad-search-btn", "n_clicks"),
    State("simbad-name", "value"),
    prevent_initial_call=True,
)
def simbad_name_search(n, name):
    if not n or not name:
        return no_update
    result = safe_simbad("object", name=name)
    if isinstance(result, str):
        return html.Div(className="alert alert-error", children=[f"Hata: {result}"])
    if result is None:
        return html.Div(className="alert alert-warning", children=[f"'{name}' bulunamadi."])
    return html.Div(className="section-card", style={"marginTop": "16px"}, children=[
        html.Div(className="alert alert-success", children=[f"'{name}' bulundu!"]),
        make_data_table(result),
    ])


# SIMBAD region search
@callback(
    Output("simbad-result", "children", allow_duplicate=True),
    Input("simbad-region-btn", "n_clicks"),
    State("simbad-ra", "value"),
    State("simbad-dec", "value"),
    State("simbad-radius", "value"),
    prevent_initial_call=True,
)
def simbad_region_search(n, ra, dec, radius):
    if not n:
        return no_update
    result = safe_simbad("region", ra=ra, dec=dec, radius=radius)
    if isinstance(result, str):
        return html.Div(className="alert alert-error", children=[f"Hata: {result}"])
    if result is None:
        return html.Div(className="alert alert-warning", children=["Sonuc bulunamadi."])

    children = [
        html.Div(className="alert alert-success", children=[
            f"{len(result)} nesne bulundu ({radius}° yaricap)"
        ]),
        make_data_table(result),
    ]

    # Sky plot
    ra_c = dec_c = None
    for col in result.columns:
        cl = col.lower()
        if "ra" in cl and ra_c is None: ra_c = col
        if "dec" in cl and dec_c is None: dec_c = col

    if ra_c and dec_c:
        valid = result[[ra_c, dec_c]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(valid) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=valid[ra_c], y=valid[dec_c], mode="markers",
                marker=dict(size=5, color=ACCENT, opacity=0.7),
                name="Results",
            ))
            fig.add_trace(go.Scatter(
                x=[ra], y=[dec], mode="markers",
                marker=dict(size=14, color="#f97316", symbol="x"),
                name="Center",
            ))
            fig.update_layout(**playout(
                title="SIMBAD Results", height=380,
                xaxis=dict(title="RA [deg]", autorange="reversed"),
                yaxis=dict(title="Dec [deg]"),
            ))
            children.append(dcc.Graph(figure=fig, config={"displaylogo": False}))

    return html.Div(className="section-card", style={"marginTop": "16px"}, children=children)


# ═══════════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=8050)
