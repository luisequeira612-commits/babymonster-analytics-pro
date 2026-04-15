import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="BABYMONSTER Analytics", layout="wide")

# Estilo visual pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE EXTRACCIÓN (SCRAPING) ---
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. Charts (iTunes/Apple Music)
    r_charts = requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=headers)
    soup_charts = BeautifulSoup(r_charts.text, "lxml")
    
    ww_eu, countries = [], []
    
    for table in soup_charts.find_all("table"):
        rows = table.find_all("tr")
        if not rows: continue
        h = [th.text.lower() for th in rows[0].find_all(["th", "td"])]
        
        if "worldwide" in h:
            for row in rows[1:6]:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    ww_eu.append({"Release": cols[0].text[:30], "WW Rank": cols[1].text, "EU Rank": cols[2].text})
        
        elif "country" in h or "pos" in h:
            plat = "Apple Music" if "applemusic" in table.get("id", "").lower() else "iTunes"
            for row in rows[1:201]: # Escaneo profundo de 200 puestos
                cols = row.find_all("td")
                if len(cols) >= 2:
                    c, p = cols[0].text.strip(), cols[1].text.strip()
                    if p.isdigit():
                        countries.append({"Platform": plat, "Country": c, "Rank": int(p)})

    # 2. YouTube Trending
    r_yt = requests.get("https://kworb.net/youtube/trending.html", headers=headers)
    soup_yt = BeautifulSoup(r_yt.text, "lxml")
    yt_trends = []
    for row in soup_yt.find_all("tr"):
        if "babymonster" in row.text.lower():
            cols = row.find_all("td")
            if len(cols) >= 4:
                yt_trends.append({"Video": cols[2].text.strip(), "Countries": cols[3].text.strip()})

    return pd.DataFrame(ww_eu), pd.DataFrame(countries), pd.DataFrame(yt_trends)

# --- INTERFAZ DEL DASHBOARD ---

st.title("🐉 BABYMONSTER Global Intelligence")
st.markdown(f"**Analyst:** Luis Sequeira | **Status:** Live Monitoring")

# Countdown
release_date = datetime(2026, 5, 4)
delta = release_date - datetime.now()
days = max(0, delta.days)
hours = max(0, delta.seconds // 3600)

col_time, col_refresh = st.columns([3, 1])
with col_time:
    st.metric("Countdown to 'Choom'", f"{days}d {hours}h")
with col_refresh:
    if st.button('🔄 Actualizar Datos'):
        st.rerun()

df_ww, df_ct, df_yt = fetch_data()

# Layout Principal
tab1, tab2 = st.tabs(["📈 Market Charts", "🎥 YouTube Trending"])

with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Global Summary")
        if not df_ww.empty:
            st.dataframe(df_ww, use_container_width=True, hide_index=True)
        else:
            st.info("Esperando datos globales...")

    with c2:
        st.subheader("Market Rankings (Top 200)")
        if not df_ct.empty:
            plat_filter = st.multiselect("Filtrar Plataforma", ["iTunes", "Apple Music"], default=["iTunes", "Apple Music"])
            df_f = df_ct[df_ct["Platform"].isin(plat_filter)]
            
            fig = px.bar(df_f.head(15), x="Country", y="Rank", color="Platform",
                         title="Top 15 Mejores Posiciones Actuales", barmode="group",
                         color_discrete_map={"iTunes": "#ff4b4b", "Apple Music": "#00d4ff"})
            fig.update_yaxes(autorange="reversed") # El #1 debe ser el más alto
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay canciones en el Top 200 de Kworb en este momento.")

with tab2:
    st.subheader("YouTube Global Trends")
    if not df_yt.empty:
        for _, row in df_yt.iterrows():
            with st.expander(f"📌 {row['Video']}"):
                st.write(f"**Tendencia detectada en:** {row['Countries']}")
    else:
        st.write("Sin presencia en tendencias globales actualmente.")

st.divider()
st.caption(f"© 2026 Luis Sequeira Analytics | Data Source: Kworb.net | Last Sync: {datetime.now().strftime('%H:%M:%S')}")
  
