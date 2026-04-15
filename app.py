import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="BABYMONSTER CHART GLOBAL", layout="wide")

# Estilo visual Pro - Rojo BABYMONSTER
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    h1, h2, h3 { color: #ff4b4b; text-transform: uppercase; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; padding: 10px 20px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DE DATOS (SCRAPER DETALLADO) ---
@st.cache_data(ttl=300)
def fetch_detailed_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    itunes_df, am_df, yt_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    global_tabs = {"WW Songs": [], "WW Albums": [], "EU Songs": [], "EU Albums": []}

    try:
        r = requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            if not rows: continue
            h = [th.text.lower() for th in rows[0].find_all(["th", "td"])]
            
            # 1. Identificar tablas Worldwide/European (Songs vs Albums)
            if "worldwide" in h:
                is_album = "album" in table.get("id", "").lower() or "album" in table.previous_sibling.text.lower()
                for row in rows[1:11]:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        entry = {"Release": cols[0].text[:30], "WW": cols[1].text, "EU": cols[2].text}
                        if is_album:
                            global_tabs["WW Albums"].append({"Album": entry["Release"], "Rank": entry["WW"]})
                            global_tabs["EU Albums"].append({"Album": entry["Release"], "Rank": entry["EU"]})
                        else:
                            global_tabs["WW Songs"].append({"Song": entry["Release"], "Rank": entry["WW"]})
                            global_tabs["EU Songs"].append({"Song": entry["Release"], "Rank": entry["EU"]})

            # 2. Datos para las 3 Columnas de abajo
            elif "country" in h or "pos" in h:
                is_am = "applemusic" in table.get("id", "").lower()
                data_list = []
                for row in rows[1:101]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        data_list.append({"País": cols[0].text.strip(), "Pos": cols[1].text.strip()})
                if is_am: am_df = pd.DataFrame(data_list)
                else: itunes_df = pd.DataFrame(data_list)

        # YouTube Trending
        r_yt = requests.get("https://kworb.net/youtube/trending.html", headers=headers, timeout=10)
        soup_yt = BeautifulSoup(r_yt.text, "lxml")
        yt_list = []
        for row in soup_yt.find_all("tr"):
            if "babymonster" in row.text.lower():
                cols = row.find_all("td")
                if len(cols) >= 4:
                    yt_list.append({"Video": cols[2].text.strip(), "Trending": cols[3].text.strip()})
        yt_df = pd.DataFrame(yt_list)

    except Exception as e:
        st.error(f"Error en sincronización: {e}")

    return itunes_df, am_df, yt_df, global_tabs

# --- SIDEBAR ---
with st.sidebar:
    st.title("📊 MONITOR")
    st.write(f"**Analyst:** Luis Sequeira")
    st.divider()
    release_date = datetime(2026, 5, 4)
    delta = release_date - datetime.now()
    st.metric("Días para 'Choom'", f"{max(0, delta.days)}d {max(0, delta.seconds // 3600)}h")
    if st.button('🔄 Forzar Actualización'):
        st.cache_data.clear()
        st.rerun()

# --- DASHBOARD ---
st.title("🚀 BABYMONSTER CHART GLOBAL")
df_itunes, df_am, df_yt, global_tabs = fetch_detailed_data()

# SECCIÓN NUEVA: Pestañas detalladas (Estilo Kworb)
st.subheader("🌎 Global Performance Breakdown")
t1, t2, t3, t4 = st.tabs(["🎵 WW Songs", "💿 WW Albums", "🇪🇺 EU Songs", "📀 EU Albums"])

with t1:
    st.dataframe(pd.DataFrame(global_tabs["WW Songs"]), use_container_width=True, hide_index=True)
with t2:
    st.dataframe(pd.DataFrame(global_tabs["WW Albums"]), use_container_width=True, hide_index=True)
with t3:
    st.dataframe(pd.DataFrame(global_tabs["EU Songs"]), use_container_width=True, hide_index=True)
with t4:
    st.dataframe(pd.DataFrame(global_tabs["EU Albums"]), use_container_width=True, hide_index=True)

st.divider()

# MAPA DE APOYO
if not df_itunes.empty:
    st.subheader("📍 Cobertura Geográfica (Live)")
    map_df = df_itunes.copy()
    map_df['Pos'] = pd.to_numeric(map_df['Pos'], errors='coerce')
    fig = px.choropleth(map_df, locations="País", locationmode='country names', 
                        color="Pos", color_continuous_scale="Reds_r", template="plotly_dark")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=300)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Escaneando charts...")

st.divider()

# LAS TRES COLUMNAS SOLICITADAS
col_it, col_am, col_yt = st.columns(3)

with col_it:
    st.subheader("🍎 iTunes")
    st.dataframe(df_itunes, hide_index=True, use_container_width=True, height=400)

with col_am:
    st.subheader("🎵 Apple Music")
    st.dataframe(df_am, hide_index=True, use_container_width=True, height=400)

with col_yt:
    st.subheader("🔥 YouTube Trending")
    if not df_yt.empty:
        for _, row in df_yt.iterrows():
            with st.expander(f"🎥 {row['Video'][:25]}..."):
                st.write(f"Tendencia en: {row['Trending']}")
    else:
        st.write("Sin tendencias actuales.")

st.divider()
st.markdown("<p style='text-align: center;'>© 2026 <b>Luis Sequeira</b> | Global Chart System</p>", unsafe_allow_html=True)
