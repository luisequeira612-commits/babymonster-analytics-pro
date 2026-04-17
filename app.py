import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Analytics PRO", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main {background-color: #0d1117;}
h1 {text-align:center; color:#ff4b4b;}
.block-container {padding-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<h1>BABYMONSTER Analytics Dashboard</h1>
<p style='text-align:center; color:gray;'>
Global charts + streaming + viral impact
</p>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Configuración")
auto = st.sidebar.toggle("Auto Refresh (60s)")

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
                data.append({
                    "Canción": cols[0].text.strip(),
                    "País": cols[1].text.strip(),
                    "Posición": cols[2].text.strip(),
                    "Plataforma": "iTunes"
                })

        if not data:
            return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

        df = pd.DataFrame(data)
        df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")
        return df

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- FETCH SPOTIFY ----------------
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
                try:
                    artist = cols[2].text.strip()
                    if "babymonster" in artist.lower():
                        data.append({
                            "Canción": cols[1].text.strip(),
                            "País": "Global",
                            "Posición": int(cols[0].text.strip()),
                            "Plataforma": "Spotify"
                        })
                except:
                    continue

        if not data:
            return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

        return pd.DataFrame(data)

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- BILLBOARD GLOBAL 200 ----------------
@st.cache_data(ttl=300)
def fetch_billboard_global():
    url = "https://www.billboard.com/charts/billboard-global-200/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []
        songs = soup.select("li ul li h3")

        for i, s in enumerate(songs):
            title = s.text.strip()
            if "babymonster" in title.lower():
                data.append({
                    "Canción": title,
                    "País": "Global",
                    "Posición": i + 1,
                    "Plataforma": "BB Global 200"
                })

        return pd.DataFrame(data, columns=["Canción","País","Posición","Plataforma"])

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- BILLBOARD EXCL US ----------------
@st.cache_data(ttl=300)
def fetch_billboard_excl():
    url = "https://www.billboard.com/charts/billboard-global-excl-us/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []
        songs = soup.select("li ul li h3")

        for i, s in enumerate(songs):
            title = s.text.strip()
            if "babymonster" in title.lower():
                data.append({
                    "Canción": title,
                    "País": "Global",
                    "Posición": i + 1,
                    "Plataforma": "BB Excl US"
                })

        return pd.DataFrame(data, columns=["Canción","País","Posición","Plataforma"])

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- CIRCLE ----------------
@st.cache_data(ttl=300)
def fetch_circle():
    url = "https://circlechart.kr/page_chart/onoff.circle?nationGbn=T&serviceGbn=ALL"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []
        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")

            if len(cols) >= 5:
                try:
                    artist = cols[3].text.strip()
                    if "babymonster" in artist.lower():
                        data.append({
                            "Canción": cols[2].text.strip(),
                            "País": "Korea",
                            "Posición": int(cols[0].text.strip()),
                            "Plataforma": "Circle"
                        })
                except:
                    continue

        return pd.DataFrame(data, columns=["Canción","País","Posición","Plataforma"])

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- YOUTUBE (FIXED) ----------------
@st.cache_data(ttl=300)
def fetch_youtube():
    url = "https://kworb.net/youtube/trending.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 5:
                try:
                    title = cols[2].text.strip()
                    views = cols[3].text.strip().replace(",", "")

                    if "babymonster" in title.lower():
                        data.append({
                            "Canción": title,
                            "Views": int(views)
                        })
                except:
                    continue

        if not data:
            return pd.DataFrame(columns=["Canción","Views"])

        return pd.DataFrame(data)

    except:
        return pd.DataFrame(columns=["Canción","Views"])

# ---------------- LOAD ----------------
with st.spinner("Cargando datos..."):
    df_all = pd.concat([
        fetch_itunes(),
        fetch_spotify(),
        fetch_billboard_global(),
        fetch_billboard_excl(),
        fetch_circle()
    ], ignore_index=True)

    df_yt = fetch_youtube()

df_all["Posición"] = pd.to_numeric(df_all["Posición"], errors="coerce")

if df_all.empty:
    st.error("No se pudieron cargar datos")
    st.stop()

# ---------------- SELECT ----------------
songs = df_all["Canción"].value_counts().index.tolist()
selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df_all[df_all["Canción"] == selected_song]

# 🔥 PROTECCIÓN YOUTUBE
if "Canción" in df_yt.columns:
    yt_filtered = df_yt[df_yt["Canción"].str.contains(selected_song, case=False, na=False)]
else:
    yt_filtered = pd.DataFrame(columns=["Canción","Views"])

# ---------------- SCORE ----------------
weights = {
    "Spotify": 1.0,
    "iTunes": 0.7,
    "BB Global 200": 2.0,
    "BB Excl US": 1.8,
    "Circle": 1.5
}

def calculate_score(filtered, yt_filtered):
    total = 0

    for platform, weight in weights.items():
        subset = filtered[filtered["Plataforma"] == platform]
        total += ((100 - subset["Posición"].fillna(100)).sum()) * weight

    yt_score = yt_filtered["Views"].sum() / 1_000_000 if not yt_filtered.empty else 0

    return total + yt_score

score = calculate_score(filtered, yt_filtered)

# ---------------- METRICS ----------------
st.subheader(selected_song)

col1, col2, col3, col4 = st.columns(4)

col1.metric("🏆 Mejor", int(filtered["Posición"].min()))
col2.metric("🔥 Top 10", int((filtered["Posición"] <= 10).sum()))
col3.metric("📊 Promedio", round(filtered["Posición"].mean(),1))
col4.metric("🌐 Score", int(score))

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🎥 YouTube", "🏆 Ranking"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

    try:
        fig = px.choropleth(
            filtered,
            locations="País",
            locationmode="country names",
            color="Posición",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Mapa no disponible")

with tab2:
    if yt_filtered.empty:
        st.info("📭 No hay videos en trending")
    else:
        st.dataframe(yt_filtered)
        st.metric("Views", int(yt_filtered["Views"].sum()))

with tab3:
    scores = []

    for song in songs:
        f = df_all[df_all["Canción"] == song]

        if "Canción" in df_yt.columns:
            yt_f = df_yt[df_yt["Canción"].str.contains(song, case=False, na=False)]
        else:
            yt_f = pd.DataFrame(columns=["Canción","Views"])

        total = calculate_score(f, yt_f)
        scores.append({"Canción": song, "Score": total})

    ranking_df = pd.DataFrame(scores).sort_values("Score", ascending=False)

    st.dataframe(ranking_df, use_container_width=True)

    fig = px.bar(ranking_df.head(10), x="Canción", y="Score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
if auto:
    time.sleep(60)
    st.rerun()
