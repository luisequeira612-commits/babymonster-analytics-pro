import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- ITUNES / APPLE MUSIC ----------------
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

# ---------------- YOUTUBE TRENDING ----------------
@st.cache_data(ttl=300)
def fetch_youtube():
    url = "https://kworb.net/youtube/trending.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 4:
                title = cols[2].text.strip()
                trend = cols[3].text.strip()

                if "babymonster" in title.lower():
                    data.append({
                        "Canción": title,
                        "País": trend,
                        "Posición": 1,
                        "Plataforma": "YouTube"
                    })

        return pd.DataFrame(data)

    except:
        return pd.DataFrame()

# ---------------- SPOTIFY (BÁSICO) ----------------
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
                song = cols[1].text.strip()
                artist = cols[2].text.strip()
                pos = cols[0].text.strip()

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
st.title("🚀 BABYMONSTER CHARTS (MULTI-PLATFORM)")

st.write("iTunes + Apple Music + YouTube + Spotify")

# ---------------- CARGAR DATOS ----------------
df_itunes = fetch_itunes()
df_yt = fetch_youtube()
df_spotify = fetch_spotify()

# combinar todo
df = pd.concat([df_itunes, df_yt, df_spotify], ignore_index=True)

if df.empty:
    st.error("No se pudieron cargar datos")
    st.stop()

# ---------------- SELECTOR ----------------
songs = sorted(df["Canción"].dropna().unique())

selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df[df["Canción"] == selected_song]

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
    (filtered["Plataforma"] == "YouTube").sum() * 3 +
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

# ---------------- INSIGHT ----------------
st.subheader("🧠 Insight")

if not filtered.empty:
    if score > 50:
        st.success("🔥 IMPACTO GLOBAL FUERTE")
    elif score > 20:
        st.info("Buen rendimiento multi-plataforma")
    else:
        st.warning("Impacto bajo o inicial")
