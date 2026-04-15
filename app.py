import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import os
import time
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- ESTILO PRO ----------------
st.markdown("""
<style>
.main {
    background-color: #0d1117;
}
h1 {
    color: #ff4b4b;
    text-align: center;
}
.stMetric {
    background-color: #161b22;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HISTORIAL YOUTUBE ----------------
def save_youtube_history(df):
    if df.empty:
        return

    df_copy = df.copy()
    df_copy["timestamp"] = datetime.now()

    file = "yt_history.csv"

    if not os.path.exists(file):
        df_copy.to_csv(file, index=False)
    else:
        df_copy.to_csv(file, mode="a", header=False, index=False)

def load_youtube_history():
    file = "yt_history.csv"

    if os.path.exists(file):
        df = pd.read_csv(file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    return pd.DataFrame()

# ---------------- ITUNES ----------------
@st.cache_data(ttl=300)
def fetch_itunes():
    url = "https://kworb.net/itunes/artist/babymonster.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")

            for row in rows[1:]:
                cols = row.find_all("td")

                if len(cols) >= 3:
                    song = cols[0].text.strip()
                    country = cols[1].text.strip()
                    pos = cols[2].text.strip()

                    if song and len(song) > 2:
                        data.append({
                            "Canción": song,
                            "País": country,
                            "Posición": pos,
                            "Plataforma": "iTunes/Apple Music"
                        })

        df = pd.DataFrame(data)

        if not df.empty:
            df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

        return df

    except:
        return pd.DataFrame()

# ---------------- YOUTUBE AVANZADO ----------------
@st.cache_data(ttl=300)
def fetch_youtube():
    urls = {
        "Global": "https://kworb.net/youtube/trending.html",
        "USA": "https://kworb.net/youtube/trending_us.html",
        "Japan": "https://kworb.net/youtube/trending_jp.html",
        "Korea": "https://kworb.net/youtube/trending_kr.html"
    }

    data = []

    for region, url in urls.items():
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, "lxml")

            for row in soup.find_all("tr"):
                cols = row.find_all("td")

                if len(cols) >= 5:
                    title = cols[2].text.strip()
                    views = cols[3].text.strip()

                    if "babymonster" in title.lower():
                        data.append({
                            "Canción": title,
                            "Región": region,
                            "Views": views,
                            "Plataforma": "YouTube"
                        })

        except:
            continue

    df = pd.DataFrame(data)

    if not df.empty:
        df["Views"] = df["Views"].str.replace(",", "")
        df["Views"] = pd.to_numeric(df["Views"], errors="coerce")

    return df

# ---------------- SPOTIFY ----------------
@st.cache_data(ttl=300)
def fetch_spotify():
    url = "https://kworb.net/spotify/country/global_daily.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 5:
                pos = cols[0].text.strip()
                song = cols[1].text.strip()
                artist = cols[2].text.strip()

                if "babymonster" in artist.lower():
                    data.append({
                        "Canción": song,
                        "País": "Global",
                        "Posición": pos,
                        "Plataforma": "Spotify"
                    })

        df = pd.DataFrame(data)

        if not df.empty:
            df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

        return df

    except:
        return pd.DataFrame()

# ---------------- UI ----------------
st.title("🚀 BABYMONSTER CHARTS")

st.sidebar.title("⚙️ Configuración")
auto = st.sidebar.toggle("⏱️ Auto Refresh (60s)")

# ---------------- DATA ----------------
df_itunes = fetch_itunes()
df_yt = fetch_youtube()
df_spotify = fetch_spotify()

# guardar historial yt
save_youtube_history(df_yt)

df_all = pd.concat([df_itunes, df_spotify], ignore_index=True)

# ---------------- SELECTOR ----------------
songs = sorted(df_all["Canción"].dropna().unique())

if not songs:
    st.error("No hay canciones disponibles")
    st.stop()

selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df_all[df_all["Canción"] == selected_song]

# ---------------- RESULTADOS ----------------
st.subheader(f"🌍 {selected_song}")

col1, col2 = st.columns([2,1])

with col1:
    st.dataframe(filtered, use_container_width=True)

with col2:
    top1 = (filtered["Posición"] == 1).sum()
    top10 = (filtered["Posición"] <= 10).sum()
    avg = filtered["Posición"].mean()

    st.metric("🥇 #1", top1)
    st.metric("🔥 Top 10", top10)
    st.metric("📊 Promedio", round(avg,1) if not pd.isna(avg) else 0)

# ---------------- GLOBAL SCORE ----------------
st.subheader("🌐 GLOBAL SCORE")

score = (
    (filtered["Plataforma"] == "iTunes/Apple Music").sum() * 2 +
    (filtered["Plataforma"] == "Spotify").sum() * 2
)

st.metric("Score Global", score)

# ---------------- MAPA ----------------
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
    st.warning("Mapa no disponible")

# ---------------- YOUTUBE ----------------
st.subheader("🔥 YouTube Trending")

if df_yt.empty:
    st.info("📭 No hay videos en trending")
else:
    st.dataframe(df_yt, use_container_width=True)

    st.metric("📊 Apariciones", len(df_yt))
    st.metric("👁️ Total Views", int(df_yt["Views"].sum()))

# ---------------- HISTORIAL ----------------
st.subheader("📈 Evolución de Views")

history_df = load_youtube_history()

if not history_df.empty:

    grouped = history_df.groupby("timestamp")["Views"].sum().reset_index()

    fig = px.line(
        grouped,
        x="timestamp",
        y="Views",
        title="Views en el tiempo",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Aún no hay suficiente historial")

# ---------------- INSIGHT ----------------
st.subheader("🧠 Insight")

if not filtered.empty:
    if score > 50:
        st.success("🔥 IMPACTO GLOBAL FUERTE")
    elif score > 20:
        st.info("Buen rendimiento")
    else:
        st.warning("Impacto inicial")

# ---------------- AUTO REFRESH ----------------
if auto:
    time.sleep(60)
    st.rerun()
