import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Global Charts", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- GLOBAL CLEANER ----------------
def clean_text(x):
    return str(x).lower().strip()

def safe_df(cols):
    return pd.DataFrame(columns=cols)

def safe_num(series):
    return pd.to_numeric(series, errors="coerce")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
.stApp {background:#0b0f17;}
h1 {text-align:center; color:#ff2e2e;}
[data-testid="stMetric"] {
    background:#161b22;
    border-radius:12px;
    border:1px solid #30363d;
    padding:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 BABYMONSTER GLOBAL CHARTS")

# ---------------- FETCH FUNCTIONS ----------------

@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        soup = BeautifulSoup(
            requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=HEADERS).text,
            "lxml"
        )

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3:

                # 🔥 FIX REAL KWORB DIRTY TEXT
                song_tag = cols[0].find("a")
                song = song_tag.text if song_tag else cols[0].text

                country = cols[1].text
                pos = cols[2].text

                song = clean_text(song)
                country = clean_text(country)

                data.append({
                    "Canción": song,
                    "País": country,
                    "Posición": pos,
                    "Plataforma": "itunes"
                })

        df = pd.DataFrame(data)
        if df.empty:
            return safe_df(["Canción","País","Posición","Plataforma"])

        df["Posición"] = safe_num(df["Posición"])
        return df

    except:
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        soup = BeautifulSoup(
            requests.get("https://kworb.net/spotify/country/global_daily.html", headers=HEADERS).text,
            "lxml"
        )

        data = []

        for r in soup.find_all("tr"):
            c = r.find_all("td")
            if len(c) >= 5:
                try:
                    artist = c[2].text.lower()
                    if "babymonster" in artist:
                        data.append({
                            "Canción": clean_text(c[1].text),
                            "País": "global",
                            "Posición": int(c[0].text),
                            "Plataforma": "spotify"
                        })
                except:
                    continue

        return pd.DataFrame(data)

    except:
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_billboard():
    try:
        soup = BeautifulSoup(
            requests.get("https://www.billboard.com/charts/billboard-global-200/", headers=HEADERS).text,
            "lxml"
        )

        data = []
        for i, s in enumerate(soup.select("h3")):
            try:
                t = clean_text(s.text)
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
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        soup = BeautifulSoup(
            requests.get("https://kworb.net/youtube/trending.html", headers=HEADERS).text,
            "lxml"
        )

        data = []

        for r in soup.find_all("tr"):
            c = r.find_all("td")
            if len(c) >= 5:
                try:
                    title = clean_text(c[2].text)
                    views = c[3].text.replace(",", "")

                    if views.isdigit() and "babymonster" in title:
                        data.append({
                            "Canción": title,
                            "Views": int(views)
                        })
                except:
                    continue

        return pd.DataFrame(data)

    except:
        return safe_df(["Canción","Views"])

# ---------------- LOAD DATA ----------------
df = pd.concat([
    fetch_itunes(),
    fetch_spotify(),
    fetch_billboard()
], ignore_index=True)

yt = fetch_youtube()

df["Posición"] = safe_num(df["Posición"])

if df.empty:
    st.error("No data available")
    st.stop()

# ---------------- SONG SELECT ----------------
songs = df["Canción"].dropna().unique().tolist()
selected = st.selectbox("🎵 Select song", songs)

# 🔥 SMART MATCH (NO EXACT BUGS)
filtered = df[df["Canción"].apply(lambda x: selected in str(x))]

yt_filtered = yt[
    yt["Canción"].apply(lambda x: selected in str(x))
] if not yt.empty else safe_df(["Canción","Views"])

# ---------------- SCORE ----------------
def score(df, yt):
    base = (100 - df["Posición"].fillna(100)).sum() if not df.empty else 0
    yt_score = yt["Views"].sum() / 1_000_000 if not yt.empty else 0
    return base + yt_score

total_score = score(filtered, yt_filtered)

# ---------------- METRICS SAFE ----------------
pos = filtered["Posición"].dropna()

if len(pos) == 0:
    best = top10 = avg = 0
else:
    best = int(pos.min())
    top10 = int((pos <= 10).sum())
    avg = round(pos.mean(), 1)

st.subheader(selected)

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
        f = df[df["Canción"].apply(lambda x: s in str(x))]
        y = yt[yt["Canción"].apply(lambda x: s in str(x))] if not yt.empty else safe_df(["Canción","Views"])

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
