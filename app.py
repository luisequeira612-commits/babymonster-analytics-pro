import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Global Charts", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- STYLE SIMPLE PERO LIMPIO ----------------
st.markdown("""
<style>
.stApp {background:#0b0f17;}
h1 {text-align:center; color:#ff2e2e;}
[data-testid="stMetric"] {
    background:#161b22;
    border:1px solid #30363d;
    border-radius:12px;
    padding:12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 BABYMONSTER GLOBAL CHARTS")

# ---------------- SAFE HELPERS ----------------
def safe_df(columns):
    return pd.DataFrame(columns=columns)

def clean_position(series):
    return pd.to_numeric(series, errors="coerce")

# ---------------- SCRAPERS ----------------
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        soup = BeautifulSoup(requests.get(
            "https://kworb.net/itunes/artist/babymonster.html",
            headers=HEADERS
        ).text, "lxml")

        data = []
        for r in soup.find_all("tr"):
            c = r.find_all("td")
            if len(c) >= 3:
                data.append({
                    "Canción": c[0].text.strip(),
                    "País": c[1].text.strip(),
                    "Posición": c[2].text.strip(),
                    "Plataforma": "iTunes"
                })

        df = pd.DataFrame(data)
        if df.empty:
            return safe_df(["Canción","País","Posición","Plataforma"])

        df["Posición"] = clean_position(df["Posición"])
        return df

    except:
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        soup = BeautifulSoup(requests.get(
            "https://kworb.net/spotify/country/global_daily.html",
            headers=HEADERS
        ).text, "lxml")

        data = []
        for r in soup.find_all("tr"):
            c = r.find_all("td")
            if len(c) >= 5:
                try:
                    if "babymonster" in c[2].text.lower():
                        data.append({
                            "Canción": c[1].text.strip(),
                            "País": "Global",
                            "Posición": int(c[0].text.strip()),
                            "Plataforma": "Spotify"
                        })
                except:
                    continue

        return pd.DataFrame(data)

    except:
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_billboard():
    try:
        soup = BeautifulSoup(requests.get(
            "https://www.billboard.com/charts/billboard-global-200/",
            headers=HEADERS
        ).text, "lxml")

        data = []
        for i, s in enumerate(soup.select("h3")):
            try:
                if "babymonster" in s.text.lower():
                    data.append({
                        "Canción": s.text.strip(),
                        "País": "Global",
                        "Posición": i + 1,
                        "Plataforma": "BB Global 200"
                    })
            except:
                continue

        return pd.DataFrame(data)

    except:
        return safe_df(["Canción","País","Posición","Plataforma"])


@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        soup = BeautifulSoup(requests.get(
            "https://kworb.net/youtube/trending.html",
            headers=HEADERS
        ).text, "lxml")

        data = []
        for r in soup.find_all("tr"):
            c = r.find_all("td")
            if len(c) >= 5:
                try:
                    title = c[2].text.strip()
                    views = c[3].text.strip().replace(",", "")
                    if views.isdigit():
                        if "babymonster" in title.lower():
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

# asegurar columnas
if "Posición" in df.columns:
    df["Posición"] = clean_position(df["Posición"])

if df.empty:
    st.warning("No data available")
    st.stop()

songs = df["Canción"].dropna().unique().tolist()
selected = st.selectbox("🎵 Song", songs)

filtered = df[df["Canción"] == selected]

# ---------------- SAFE YOUTUBE MATCH ----------------
if not yt.empty:
    yt_filtered = yt[
        yt["Canción"].astype(str).str.contains(
            str(selected), case=False, na=False, regex=False
        )
    ]
else:
    yt_filtered = safe_df(["Canción","Views"])

# ---------------- SAFE SCORE ----------------
def calc_score(df, yt):
    if df.empty:
        base = 0
    else:
        base = (100 - df["Posición"].fillna(100)).sum()

    yt_score = yt["Views"].sum() / 1_000_000 if not yt.empty else 0
    return base + yt_score

score = calc_score(filtered, yt_filtered)

# ---------------- SAFE METRICS ----------------
pos = filtered["Posición"].dropna() if "Posición" in filtered else pd.Series([])

if len(pos) == 0:
    best = 0
    top10 = 0
    avg = 0
else:
    best = int(pos.min())
    top10 = int((pos <= 10).sum())
    avg = round(pos.mean(), 1)

# ---------------- UI ----------------
st.subheader(selected)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best", best)
c2.metric("🔥 Top 10", top10)
c3.metric("📊 Avg", avg)
c4.metric("🌐 Score", int(score) if pd.notna(score) else 0)

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
        f = df[df["Canción"] == s]
        y = yt[yt["Canción"].astype(str).str.contains(s, case=False, regex=False)] if not yt.empty else pd.DataFrame()

        ranking.append({
            "Canción": s,
            "Score": calc_score(f, y)
        })

    rank_df = pd.DataFrame(ranking).sort_values("Score", ascending=False)

    st.dataframe(rank_df, use_container_width=True)

    fig = px.bar(rank_df.head(10), x="Canción", y="Score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
if st.sidebar.toggle("Auto Refresh 60s"):
    time.sleep(60)
    st.rerun()
