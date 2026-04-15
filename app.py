import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px

# Configuración de la página con el nuevo nombre
st.set_page_config(page_title="BABYMONSTER CHART GLOBAL", layout="wide")

# Estilo visual Pro
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    h1, h2, h3 { color: #ff4b4b; } /* Color rojo BABYMONSTER */
    </style>
    """, unsafe_allow_html=True)

# --- SCRAPING ENGINE ---
@st.cache_data(ttl=600)
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r_charts = requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=headers, timeout=10)
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
                for row in rows[1:201]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        c, p = cols[0].text.strip(), cols[1].text.strip()
                        if p.isdigit(): countries.append({"Platform": plat, "Country": c, "Rank": int(p)})
        df_ww, df_ct = pd.DataFrame(ww_eu), pd.DataFrame(countries)
    except:
        df_ww, df_ct = pd.DataFrame(), pd.DataFrame()

    try:
        r_yt = requests.get("https://kworb.net/youtube/trending.html", headers=headers, timeout=10)
        soup_yt = BeautifulSoup(r_yt.text, "lxml")
        yt_trends = []
        for row in soup_yt.find_all("tr"):
            if "babymonster" in row.text.lower():
                cols = row.find_all("td")
                if len(cols) >= 4:
                    yt_trends.append({"Video": cols[2].text.strip(), "Countries": cols[3].text.strip(), "Count": len(cols[3].text.split(','))})
        df_yt = pd.DataFrame(yt_trends)
    except:
        df_yt = pd.DataFrame()

    return df_ww, df_ct, df_yt

# --- SIDEBAR ---
with st.sidebar:
    st.title("📊 MONITOR")
    st.write(f"**Dev:** Luis Sequeira")
    st.divider()
    
    release_date = datetime(2026, 5, 4)
    delta = release_date - datetime.now()
    st.metric("Días para 'Choom'", f"{max(0, delta.days)}d {max(0, delta.seconds // 3600)}h")
    
    st.divider()
    if st.button('🔄 Refresh Charts'):
        st.cache_data.clear()
        st.rerun()

# --- MAIN DASHBOARD ---
df_ww, df_ct, df_yt = fetch_data()

# Título Principal Actualizado
st.title("🚀 BABYMONSTER CHART GLOBAL")
st.caption(f"Actualización automática | Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

# Sección 1: Mapa e Impacto
col_map, col_sum = st.columns([2, 1])

with col_map:
    st.subheader("📍 Presencia Global en Tiempo Real")
    if not df_ct.empty:
        fig_map = px.choropleth(df_ct.groupby("Country")["Rank"].min().reset_index(), 
                                locations="Country", locationmode='country names',
                                color="Rank", color_continuous_scale="Reds_r",
                                template="plotly_dark")
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Escaneando charts de Kworb...")

with col_sum:
    st.subheader("🌎 Global Rankings")
    if not df_ww.empty:
        st.dataframe(df_ww, hide_index=True)
    else:
        st.write("Sin datos mundiales hoy.")

st.divider()

# Sección 2: Tabs de Análisis
tab_charts, tab_yt = st.tabs(["📊 Análisis de Charts", "🔥 Tendencias YT"])

with tab_charts:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("iTunes vs Apple Music")
        if not df_ct.empty:
            fig_box = px.box(df_ct, x="Platform", y="Rank", color="Platform",
                              color_discrete_map={"iTunes": "#ff4b4b", "Apple Music": "#ff8e8e"})
            fig_box.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_box, use_container_width=True)
    
    with c2:
        st.subheader("Top 20 Países")
        if not df_ct.empty:
            df_top = df_ct.sort_values("Rank").head(20)
            fig_bar = px.bar(df_top, x="Country", y="Rank", color="Platform", barmode="group")
            fig_bar.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_bar, use_container_width=True)

with tab_yt:
    if not df_yt.empty:
        st.subheader("Impacto Viral (YouTube)")
        fig_yt = px.scatter(df_yt, x="Video", y="Count", size="Count", color="Video", title="Países en Tendencia")
        st.plotly_chart(fig_yt, use_container_width=True)
    else:
        st.info("No hay videos en tendencia global por ahora.")

st.divider()
st.markdown(f"<p style='text-align: center;'>© 2026 <b>Luis Sequeira</b> | Powering BABYMONSTER Analytics</p>", unsafe_allow_html=True)
        
  
