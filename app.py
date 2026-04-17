import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time
import difflib

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER GLOBAL INTELLIGENCE", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= CORE NORMALIZATION =================
def norm(x):
    return " ".join(str(x).lower().split())

def safe_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except:
        return None

def empty_df():
    return pd.DataFrame(columns=["song","country","position","platform"])

# ================= FUZZY MATCH ENGINE =================
def best_match(song, df):
    if df.empty:
        return df

    song = norm(song)
    candidates = df["song"].dropna().unique()

    match = difflib.get_close_matches(song, candidates, n=1, cutoff=0.4)

    if not match:
        return df.iloc[0:0]

    return df[df["song"] == match[0]]

# ================= SAFE SCRAPING (FALLBACK ONLY) =================
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if not cols:
                continue

            # 🎯 anchor-based extraction
            a = row.find("a")
            if not a:
                continue

            song = norm(a.text)

            if not song or song.startswith("#"):
                continue

            country = norm(cols[1].text) if len(cols) > 1 else "unknown"
            pos = safe_int(cols[2].text) if len(cols) > 2 else None

            data.append({
                "song": song,
                "country": country,
                "position": pos,
                "platform": "itunes"
            })

        return pd.DataFrame(data) if data else empty_df()

    except:
        return empty_df()

@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        url = "https://kworb.net/spotify/country/global_daily.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            c = row.find_all("td")
            if len(c) < 5:
                continue

            artist = norm(c[2].text)
            if "babymonster" not in artist:
                continue

            data.append({
                "song": norm(c[1].text),
                "country": "global",
                "position": safe_int(c[0].text),
                "platform": "spotify"
            })

        return pd.DataFrame(data) if data else empty_df()

    except:
        return empty_df()

@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            c = row.find_all("td")
            if len(c) < 5:
                continue

            title = norm(c[2].text)
            views = safe_int(c[3].text)

            if "babymonster" not in title:
                continue

            data.append({
                "song": title,
                "views": views
            })

        return pd.DataFrame(data) if data else empty_df()

    except:
        return empty_df()

# ================= LOAD DATA =================
df = pd.concat([
    fetch_itunes(),
    fetch_spotify()
], ignore_index=True)

yt = fetch_youtube()

if df.empty:
    st.error("No data available (sources may be blocked or changed)")
    st.stop()

# ================= SONG LIST =================
songs = df["song"].dropna().unique().tolist()

selected = st.selectbox("🎵 Select song", songs)

# ================= MATCHING (ROBUST) =================
filtered = best_match(selected, df)
yt_filtered = best_match(selected, yt)

# ================= SCORE ENGINE =================
def score(df, yt):
    base = (100 - df["position"].fillna(100)).sum() if not df.empty else 0
    yt_score = yt["views"].sum() / 1_000_000 if not yt.empty else 0
    return base + yt_score

total_score = score(filtered, yt_filtered)

# ================= SAFE METRICS =================
pos = filtered["position"].dropna()

best = int(pos.min()) if len(pos) else 0
top10 = int((pos <= 10).sum()) if len(pos) else 0
avg = round(pos.mean(), 1) if len(pos) else 0

# ================= UI =================
st.title("🔥 BABYMONSTER GLOBAL INTELLIGENCE (STABLE VERSION)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best", best)
c2.metric("🔥 Top 10", top10)
c3.metric("📊 Avg", avg)
c4.metric("🌐 Score", int(total_score))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Data", "🎥 YouTube", "🏆 Ranking"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    st.dataframe(yt_filtered if not yt_filtered.empty else pd.DataFrame())

with tab3:
    ranking = []

    for s in songs:
        f = best_match(s, df)
        y = best_match(s, yt)

        ranking.append({
            "song": s,
            "score": score(f, y)
        })

    rank_df = pd.DataFrame(ranking).sort_values("score", ascending=False)

    st.dataframe(rank_df, use_container_width=True)

    fig = px.bar(rank_df.head(10), x="song", y="score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ================= AUTO REFRESH =================
if st.sidebar.toggle("Auto refresh"):
    time.sleep(60)
    st.rerun()
