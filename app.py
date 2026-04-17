import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Global Charts", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- GLOBAL NORMALIZER ----------------
def clean(x):
    return str(x).lower().strip()

def to_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except:
        return None

def safe_df():
    return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

# ---------------- CORE EXTRACTION ENGINE ----------------
def extract_song(row):
    """
    🔥 anchor-based extraction (ROBUST)
    """
    # prioridad 1: links de canción
    a = row.select_one('a[href*="song"]')
    if a:
        return clean(a.text)

    # fallback: cualquier link
    a2 = row.find("a")
    if a2:
        return clean(a2.text)

    # último fallback
    return None

def extract_columns(row):
    cols = row.find_all("td")

    country = cols[1].text if len(cols) > 1 else "unknown"
    pos = cols[2].text if len(cols) > 2 else None

    return clean(country), to_int(pos)

# ---------------- SCRAPERS ----------------

@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            try:
                song = extract_song(row)
                if not song:
                    continue

                country, pos = extract_columns(row)

                data.append({
                    "Canción": song,
                    "País": country,
                    "Posición": pos,
                    "Plataforma": "itunes"
                })

            except:
                continue

        df = pd.DataFrame(data)
        if df.empty:
            return safe_df()

        df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")
        return df

    except:
        return safe_df()


@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        url = "https://kworb.net/spotify/country/global_daily.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                artist = clean(cols[2].text)

                if "babymonster" not in artist:
                    continue

                data.append({
                    "Canción": clean(cols[1].text),
                    "País": "global",
                    "Posición": to_int(cols[0].text),
                    "Plataforma": "spotify"
                })

            except:
                continue

        return pd.DataFrame(data)

    except:
        return safe_df()


@st.cache_data(ttl=300)
def fetch_billboard():
    try:
        url = "https://www.billboard.com/charts/billboard-global-200/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for i, h in enumerate(soup.select("h3")):
            try:
                t = clean(h.text)

                if "babymonster" in t:
                    data.append({
                        "Canción": t,
                        "País": "global",
                        "Posición": i + 1,
                        "Plataforma": "bb_global"
                    })
            except:
                continue

        return pd.DataFrame(data)

    except:
        return safe_df()


@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                title = clean(cols[2].text)
                views = to_int(cols[3].text)

                if "babymonster" not in title:
                    continue

                if views is None:
                    continue

                data.append({
                    "Canción": title,
                    "Views": views
                })

            except:
                continue

        return pd.DataFrame(data)

    except:
        return safe_df()

# ---------------- LOAD DATA ----------------
df = pd.concat([
    fetch_itunes(),
    fetch_spotify(),
    fetch_billboard()
], ignore_index=True)

yt = fetch_youtube()

df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

if df.empty:
    st.error("No data available")
    st.stop()

# ---------------- SONG SELECT ----------------
songs = df["Canción"].dropna().unique().tolist()
selected = st.selectbox("🎵 Select song", songs)

# 🔥 SMART MATCH ENGINE (ROBUST)
def match(df, song):
    return df[df["Canción"].str.contains(song, na=False, regex=False)]

filtered = match(df, selected)
yt_filtered = match(yt, selected) if not yt.empty else safe_df()

# ---------------- SCORE ENGINE ----------------
def score(df, yt):
    base = (100 - df["Posición"].fillna(100)).sum() if not df.empty else 0
    yt_score = yt["Views"].sum() / 1_000_000 if not yt.empty else 0
    return base + yt_score

total_score = score(filtered, yt_filtered)

# ---------------- SAFE METRICS ----------------
pos = filtered["Posición"].dropna()

if len(pos) == 0:
    best = 0
    top10 = 0
    avg = 0
else:
    best = int(pos.min())
    top10 = int((pos <= 10).sum())
    avg = round(pos.mean(), 1)

# ---------------- UI ----------------
st.title("🔥 BABYMONSTER GLOBAL CHARTS")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best", best)
c2.metric("🔥 Top 10", top10)
c3.metric("📊 Avg", avg)
c4.metric("🌐 Score", int(total_score))

st.markdown("---")

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📊 Data", "🎥 YouTube", "🏆 Ranking"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    if yt_filtered.empty:
        st.info("No YouTube data")
    else:
        st.dataframe(yt_filtered)
        st.metric("Views", int(yt_filtered["Views"].sum()))

with tab3:
    ranking = []

    for s in songs:
        f = match(df, s)
        y = match(yt, s) if not yt.empty else safe_df()

        ranking.append({
            "Canción": s,
            "Score": score(f, y)
        })

    rank_df = pd.DataFrame(ranking).sort_values("Score", ascending=False)

    st.dataframe(rank_df, use_container_width=True)

    fig = px.bar(rank_df.head(10), x="Canción", y="Score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
if st.sidebar.toggle("Auto Refresh 60s"):
    time.sleep(60)
    st.rerun()
