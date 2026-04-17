import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import sqlite3
from datetime import datetime
import re

# ================= CONFIG =================
st.set_page_config(page_title="BM Global Tracker", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}
DB = "bm_pro.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            song TEXT,
            clean_song TEXT,
            platform TEXT,
            country TEXT,
            position INTEGER,
            views INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# ================= CLEANING ENGINE =================
def clean_song(text):
    text = str(text).lower()

    # eliminar ruido típico
    noise = [
        "babymonster", "official", "mv", "m/v",
        "performance", "video", "audio", "ver", "version"
    ]

    for n in noise:
        text = text.replace(n, "")

    # eliminar símbolos
    text = re.sub(r'[^a-z0-9\s]', '', text)

    # espacios limpios
    text = " ".join(text.split())

    return text.strip()

# ================= MATCH ENGINE =================
def match_score(a, b):
    a_set = set(a.split())
    b_set = set(b.split())

    if not a_set or not b_set:
        return 0

    return len(a_set & b_set) / len(a_set | b_set)

def group_songs(df):
    groups = {}

    for song in df["clean_song"].unique():
        placed = False

        for key in groups:
            if match_score(song, key) > 0.6:
                groups[key].append(song)
                placed = True
                break

        if not placed:
            groups[song] = [song]

    mapping = {}
    for key, vals in groups.items():
        for v in vals:
            mapping[v] = key

    df["group"] = df["clean_song"].map(mapping)

    return df

# ================= HELPERS =================
def to_int(x):
    try:
        return int(str(x).replace(",", "").replace("#","").strip())
    except:
        return None

def empty():
    return pd.DataFrame(columns=["song","clean_song","platform","country","position","views"])

# ================= ITUNES =================
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            link = cols[0].find("a", href=True)
            if not link:
                continue

            href = link.get("href", "")
            song = link.text.strip()

            # 🔥 FILTRO DURO
            if not song or song.startswith("#"):
                continue
            if "spotify" in song.lower():
                continue
            if "/itunes/song/" not in href:
                continue

            data.append({
                "song": song,
                "clean_song": clean_song(song),
                "platform": "itunes",
                "country": cols[1].text.strip(),
                "position": to_int(cols[2].text),
                "views": None
            })

        return pd.DataFrame(data) if data else empty()

    except:
        return empty()

# ================= YOUTUBE =================
@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            title = cols[2].text.strip()
            views = to_int(cols[3].text)

            if "babymonster" not in title.lower():
                continue

            data.append({
                "song": title,
                "clean_song": clean_song(title),
                "platform": "youtube",
                "country": "global",
                "position": None,
                "views": views
            })

        return pd.DataFrame(data) if data else empty()

    except:
        return empty()

# ================= INIT =================
init_db()

itunes = fetch_itunes()
yt = fetch_youtube()

df = pd.concat([itunes, yt], ignore_index=True)

if df.empty:
    st.error("No data available")
    st.stop()

# ================= GROUP SONGS =================
df = group_songs(df)

# ================= SELECT =================
groups = sorted(df["group"].dropna().unique())
selected = st.selectbox("🎵 Select song", groups)

filtered = df[df["group"] == selected]

# ================= METRICS =================
pos = filtered["position"].dropna()
views = filtered["views"].fillna(0)

best = int(pos.min()) if len(pos) else 0
top10 = int((pos <= 10).sum()) if len(pos) else 0
total_views = int(views.sum())

score = (100 - pos).sum() + (total_views / 1_000_000)

# ================= UI =================
st.title("🔥 BM GLOBAL TRACKER")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best", best)
c2.metric("🔥 Top 10", top10)
c3.metric("👁️ Views", total_views)
c4.metric("🌐 Score", int(score))

st.markdown("---")

tab1, tab2 = st.tabs(["📊 Data", "📈 Performance"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    fig = px.bar(filtered,
                 x="platform",
                 y="views",
                 color="platform",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ================= INSIGHT =================
st.markdown("### 🧠 Insight")

if score > 80:
    st.success("🔥 DOMINANT")
elif score > 40:
    st.info("📈 GROWING")
else:
    st.warning("📊 EARLY STAGE")
