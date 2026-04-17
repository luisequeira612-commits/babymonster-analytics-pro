import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER GLOBAL INTELLIGENCE", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= NORMALIZATION LAYER =================
def clean(x):
    return str(x).lower().strip()

def to_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except:
        return None

def safe_df():
    return pd.DataFrame(columns=["song","country","position","platform"])

def valid_song(text):
    if not text:
        return False
    t = clean(text)
    return len(t) > 1 and not t.startswith("#")

# ================= EXTRACTION ENGINE =================
def extract_song(row):
    """
    🔥 INDUSTRY RULE:
    Only accept rows with valid song anchors
    """
    links = row.find_all("a", href=True)

    for a in links:
        if any(x in a["href"] for x in ["/song/", "/itunes/song/"]):
            if valid_song(a.text):
                return clean(a.text)

    return None

def extract_meta(row):
    cols = row.find_all("td")

    country = cols[1].text if len(cols) > 1 else "unknown"
    pos = cols[2].text if len(cols) > 2 else None

    return clean(country), to_int(pos)

# ================= SAFE SCRAPERS =================
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            song = extract_song(row)
            if not song:
                continue

            country, pos = extract_meta(row)

            data.append({
                "song": song,
                "country": country,
                "position": pos,
                "platform": "itunes"
            })

        return pd.DataFrame(data) if data else safe_df()

    except:
        return safe_df()

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

            artist = clean(c[2].text)

            if "babymonster" not in artist:
                continue

            data.append({
                "song": clean(c[1].text),
                "country": "global",
                "position": to_int(c[0].text),
                "platform": "spotify"
            })

        return pd.DataFrame(data) if data else safe_df()

    except:
        return safe_df()

@st.cache_data(ttl=300)
def fetch_billboard():
    try:
        url = "https://www.billboard.com/charts/billboard-global-200/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for i, h in enumerate(soup.select("h3")):
            t = clean(h.text)

            if "babymonster" in t:
                data.append({
                    "song": t,
                    "country": "global",
                    "position": i + 1,
                    "platform": "billboard_global_200"
                })

        return pd.DataFrame(data) if data else safe_df()

    except:
        return safe_df()

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

            title = clean(c[2].text)
            views = to_int(c[3].text)

            if "babymonster" not in title:
                continue

            if views is None:
                continue

            data.append({
                "song": title,
                "views": views
            })

        return pd.DataFrame(data) if data else safe_df()

    except:
        return safe_df()

# ================= LOAD LAYER =================
df = pd.concat([
    fetch_itunes(),
    fetch_spotify(),
    fetch_billboard()
], ignore_index=True)

yt = fetch_youtube()

if df.empty:
    st.error("No data available")
    st.stop()

# ================= MATCH ENGINE =================
songs = df["song"].dropna().unique().tolist()

selected = st.selectbox("🎵 Select song", songs)

def match(df, song):
    return df[df["song"].str.contains(song, na=False, regex=False)]

filtered = match(df, selected)
yt_filtered = match(yt, selected) if not yt.empty else safe_df()

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
st.title("🔥 BABYMONSTER GLOBAL INTELLIGENCE")

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
    if yt_filtered.empty:
        st.info("No data")
    else:
        st.dataframe(yt_filtered)
        st.metric("Views", int(yt_filtered["views"].sum()))

with tab3:
    ranking = []

    for s in songs:
        f = match(df, s)
        y = match(yt, s) if not yt.empty else safe_df()

        ranking.append({
            "song": s,
            "score": score(f, y)
        })

    rank_df = pd.DataFrame(ranking).sort_values("score", ascending=False)

    st.dataframe(rank_df, use_container_width=True)

    fig = px.bar(rank_df.head(10), x="song", y="score", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ================= AUTO REFRESH =================
if st.sidebar.toggle("Auto Refresh"):
    time.sleep(60)
    st.rerun()
