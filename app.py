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

# ---------------- HELPERS ----------------
def normalize(text):
    return str(text).lower().strip()

# ---------------- FETCH FUNCTIONS ----------------

@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

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

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

        df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")
        return df

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        url = "https://kworb.net/spotify/country/global_daily.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 5:
                try:
                    if "babymonster" in cols[2].text.lower():
                        data.append({
                            "Canción": cols[1].text.strip(),
                            "País": "Global",
                            "Posición": int(cols[0].text.strip()),
                            "Plataforma": "Spotify"
                        })
                except:
                    continue

        return pd.DataFrame(data, columns=["Canción","País","Posición","Plataforma"])

    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_billboard_global():
    try:
        url = "https://www.billboard.com/charts/billboard-global-200/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []
        for i, s in enumerate(soup.select("li ul li h3")):
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


@st.cache_data(ttl=300)
def fetch_billboard_excl():
    try:
        url = "https://www.billboard.com/charts/billboard-global-excl-us/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []
        for i, s in enumerate(soup.select("li ul li h3")):
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


@st.cache_data(ttl=300)
def fetch_circle():
    try:
        url = "https://circlechart.kr/page_chart/onoff.circle?nationGbn=T&serviceGbn=ALL"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []
        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")

            if len(cols) >= 5:
                try:
                    if "babymonster" in cols[3].text.lower():
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


@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 5:
                try:
                    title = cols[2].text.strip()
                    views = int(cols[3].text.strip().replace(",", ""))

                    if "babymonster" in title.lower():
                        data.append({"Canción": title, "Views": views})
                except:
                    continue

        return pd.DataFrame(data, columns=["Canción","Views"])

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
    st.error("No hay datos disponibles")
    st.stop()

# ---------------- SELECT ----------------
songs = df_all["Canción"].dropna().unique().tolist()
selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df_all[df_all["Canción"] == selected_song]

# 🔥 MATCHING MEJORADO (SIN REGEX)
yt_filtered = df_yt[
    df_yt["Canción"].astype(str).str.contains(
        selected_song, case=False, na=False, regex=False
    )
] if not df_yt.empty else pd.DataFrame(columns=["Canción","Views"])

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

c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Mejor", int(filtered["Posición"].min()))
c2.metric("🔥 Top 10", int((filtered["Posición"] <= 10).sum()))
c3.metric("📊 Promedio", round(filtered["Posición"].mean(),1))
c4.metric("🌐 Score", int(score))

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🎥 YouTube", "🏆 Ranking"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    if yt_filtered.empty:
        st.info("📭 No hay trending ahora mismo")
    else:
        st.dataframe(yt_filtered)
        st.metric("Views", int(yt_filtered["Views"].sum()))

with tab3:
    ranking = []

    for song in songs:
        f = df_all[df_all["Canción"] == song]

        yt_f = df_yt[
            df_yt["Canción"].astype(str).str.contains(
                song, case=False, na=False, regex=False
            )
        ] if not df_yt.empty else pd.DataFrame()

        ranking.append({
            "Canción": song,
            "Score": calculate_score(f, yt_f)
        })

    ranking_df = pd.DataFrame(ranking).sort_values("Score", ascending=False)

    st.dataframe(ranking_df, use_container_width=True)

    fig = px.bar(ranking_df.head(10), x="Canción", y="Score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
if auto:
    time.sleep(60)
    st.rerun()
