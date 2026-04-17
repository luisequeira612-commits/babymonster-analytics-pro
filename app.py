import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
from datetime import datetime
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Analytics", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main {background-color: #0d1117;}
h1 {color: #ff4b4b; text-align: center;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<h1>BABYMONSTER Analytics Dashboard</h1>
<p style='text-align:center; color:gray;'>
Real-time global performance tracking
</p>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Configuración")
auto = st.sidebar.toggle("Auto Refresh (60s)")
platform_filter = st.sidebar.multiselect(
    "Plataformas",
    ["Spotify", "iTunes"],
    default=["Spotify", "iTunes"]
)

# ---------------- FETCH ITUNES ----------------
@st.cache_data(ttl=300)
def fetch_itunes():
    url = "https://kworb.net/itunes/artist/babymonster.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 3:
                song = cols[0].text.strip()
                country = cols[1].text.strip()
                pos = cols[2].text.strip()

                if song:
                    data.append({
                        "Canción": song,
                        "País": country,
                        "Posición": pos,
                        "Plataforma": "iTunes"
                    })

        if not data:
            return pd.DataFrame(columns=["Canción", "País", "Posición", "Plataforma"])

        df = pd.DataFrame(data)
        df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

        return df

    except Exception as e:
        st.error(f"Error iTunes: {e}")
        return pd.DataFrame(columns=["Canción", "País", "Posición", "Plataforma"])

# ---------------- FETCH SPOTIFY (FIXED) ----------------
@st.cache_data(ttl=300)
def fetch_spotify():
    url = "https://kworb.net/spotify/country/global_daily.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []
        rows = soup.find_all("tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) >= 5:
                try:
                    pos = cols[0].text.strip()
                    song = cols[1].text.strip()
                    artist = cols[2].text.strip()

                    if "babymonster" in artist.lower():
                        data.append({
                            "Canción": song,
                            "País": "Global",
                            "Posición": int(pos),
                            "Plataforma": "Spotify"
                        })
                except:
                    continue

        if not data:
            return pd.DataFrame(columns=["Canción", "País", "Posición", "Plataforma"])

        df = pd.DataFrame(data)

        return df

    except Exception as e:
        st.error(f"Error Spotify: {e}")
        return pd.DataFrame(columns=["Canción", "País", "Posición", "Plataforma"])

# ---------------- LOAD DATA ----------------
with st.spinner("Cargando datos..."):
    df_itunes = fetch_itunes()
    df_spotify = fetch_spotify()

# ---------------- MERGE ----------------
df_all = pd.concat([df_itunes, df_spotify], ignore_index=True)

# 🔥 FIX GLOBAL: asegurar columna numérica
df_all["Posición"] = pd.to_numeric(df_all["Posición"], errors="coerce")

df_all = df_all[df_all["Plataforma"].isin(platform_filter)]

if df_all.empty:
    st.error("No se pudieron cargar datos. Intenta refrescar.")
    st.stop()

# ---------------- SELECT SONG ----------------
songs = df_all["Canción"].value_counts().index.tolist()
selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df_all[df_all["Canción"] == selected_song]

# ---------------- METRICS ----------------
st.subheader(selected_song)

col1, col2, col3 = st.columns(3)

best = filtered["Posición"].min()
top10 = (filtered["Posición"] <= 10).sum()
avg = filtered["Posición"].mean()

col1.metric("🏆 Mejor Posición", int(best) if not pd.isna(best) else "-")
col2.metric("🔥 Top 10", int(top10))
col3.metric("📊 Promedio", round(avg, 1) if not pd.isna(avg) else "-")

# ---------------- SCORE ----------------
score = (100 - filtered["Posición"].fillna(100)).sum()
st.metric("🌐 Global Score", int(score))

# ---------------- TABLE ----------------
st.dataframe(filtered, use_container_width=True)

# ---------------- MAP ----------------
st.subheader("📍 Mapa Global")

try:
    fig = px.choropleth(
        filtered,
        locations="País",
        locationmode="country names",
        color="Posición",
        color_continuous_scale="Reds_r",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
except:
    st.info("Mapa no disponible")

# ---------------- RANKING ----------------
st.subheader("🏆 Ranking interno")

ranking = (
    df_all.groupby("Canción")["Posición"]
    .mean()
    .sort_values()
    .reset_index()
)

st.dataframe(ranking, use_container_width=True)

# ---------------- INSIGHT ----------------
st.subheader("🧠 Insight")

if best == 1:
    st.success("🚀 Hit global (Top 1)")
elif best <= 10:
    st.info("🔥 Alto rendimiento")
else:
    st.warning("📊 Rendimiento moderado")

# ---------------- AUTO REFRESH ----------------
if auto:
    time.sleep(60)
    st.rerun()
