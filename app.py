import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import sqlite3
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="BM PRO SAAS", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

DB = "bm_pro.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song TEXT,
            platform TEXT,
            country TEXT,
            position INTEGER,
            views INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_snapshot(df):
    if df.empty:
        return

    conn = sqlite3.connect(DB)
    df["timestamp"] = datetime.now().isoformat()
    df.to_sql("snapshots", conn, if_exists="append", index=False)
    conn.close()

def load_history():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM snapshots", conn)
    conn.close()
    return df

# ================= HELPERS =================
def norm(x):
    return str(x).lower().strip()

def to_int(x):
    try:
        return int(str(x).replace(",", "").replace("#","").strip())
    except:
        return None

def empty():
    return pd.DataFrame(columns=["song","platform","country","position","views"])

# ================= ITUNES =================
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            a = row.find("a")
            if not a:
                continue

            song = norm(a.text)
            if not song or song.startswith("#"):
                continue

            cols = row.find_all("td")

            data.append({
                "song": song,
                "platform": "itunes",
                "country": cols[1].text if len(cols) > 1 else "unknown",
                "position": to_int(cols[2].text) if len(cols) > 2 else None,
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
            c = row.find_all("td")
            if len(c) < 5:
                continue

            title = norm(c[2].text)
            views = to_int(c[3].text)

            if "babymonster" not in title:
                continue

            data.append({
                "song": title,
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

save_snapshot(df)

if df.empty:
    st.error("No data available")
    st.stop()

# ================= UI HEADER =================
st.title("🔥 BM PRO SAAS")

# ================= SONGS =================
songs = sorted(df["song"].dropna().unique().tolist())
selected = st.selectbox("🎵 Select song", songs)

# ================= FILTER =================
filtered = df[df["song"].str.contains(selected, case=False, na=False)]

# ================= METRICS =================
pos = filtered["position"].dropna()
views = filtered["views"].fillna(0)

best = int(pos.min()) if len(pos) else 0
top10 = int((pos <= 10).sum()) if len(pos) else 0
total_views = int(views.sum())

score = (100 - pos).sum() + (total_views / 1_000_000)

# ================= DASHBOARD =================
c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Best Position", best)
c2.metric("🔥 Top 10", top10)
c3.metric("👁️ Views", total_views)
c4.metric("🌐 Score", int(score))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Live Data", "📈 Analytics", "🗄️ History"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    fig = px.bar(filtered,
                 x="platform",
                 y="views",
                 color="platform",
                 title="Platform Performance",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    history = load_history()

    if not history.empty:
        history["timestamp"] = pd.to_datetime(history["timestamp"])

        grouped = history.groupby("timestamp")[["views"]].sum().reset_index()

        fig = px.line(grouped,
                      x="timestamp",
                      y="views",
                      title="Growth Over Time",
                      template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No history yet")

# ================= INSIGHT ENGINE =================
st.markdown("### 🧠 Insight Engine")

if score > 80:
    st.success("🔥 DOMINANT PERFORMANCE")
elif score > 40:
    st.info("📈 STRONG PRESENCE")
else:
    st.warning("📊 EMERGING SIGNAL")

# ================= AUTO REFRESH =================
if st.sidebar.toggle("Auto Refresh"):
    st.rerun()
