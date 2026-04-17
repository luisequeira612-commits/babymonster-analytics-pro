import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px

# ================= CONFIG =================
st.set_page_config(page_title="BM Global Tracker", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= NORMALIZATION =================
def norm(x):
    return str(x).lower().strip()

def to_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except:
        return None

def empty():
    return pd.DataFrame(columns=["song","country","position","platform"])

# ================= BILLBOARD GLOBAL 200 (BASE PRINCIPAL) =================
@st.cache_data(ttl=3600)
def fetch_billboard_global_200():
    try:
        url = "https://www.billboard.com/charts/billboard-global-200/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        # Billboard estructura estable: posiciones + títulos
        titles = soup.select("li ul li h3")

        for i, t in enumerate(titles):
            song = norm(t.text)

            if not song:
                continue

            if "babymonster" in song:
                data.append({
                    "song": song,
                    "country": "global",
                    "position": i + 1,
                    "platform": "billboard_global_200"
                })

        return pd.DataFrame(data) if data else empty()

    except:
        return empty()

# ================= BILLBOARD GLOBAL EXCL US =================
@st.cache_data(ttl=3600)
def fetch_billboard_global_excl_us():
    try:
        url = "https://www.billboard.com/charts/billboard-global-excl-us/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        titles = soup.select("li ul li h3")

        for i, t in enumerate(titles):
            song = norm(t.text)

            if "babymonster" in song:
                data.append({
                    "song": song,
                    "country": "global_excl_us",
                    "position": i + 1,
                    "platform": "billboard_global_excl_us"
                })

        return pd.DataFrame(data) if data else empty()

    except:
        return empty()

# ================= CIRCLE CHART (KOREA) =================
@st.cache_data(ttl=3600)
def fetch_circle_chart():
    try:
        url = "https://circlechart.kr/"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")

        data = []

        # Circle es más complejo → fallback genérico
        for t in soup.find_all(["h3","td"]):
            text = norm(t.text)

            if "babymonster" in text:
                data.append({
                    "song": text,
                    "country": "korea",
                    "position": None,
                    "platform": "circle_chart"
                })

        return pd.DataFrame(data) if data else empty()

    except:
        return empty()

# ================= LOAD DATA =================
df = pd.concat([
    fetch_billboard_global_200(),
    fetch_billboard_global_excl_us(),
    fetch_circle_chart()
], ignore_index=True)

if df.empty:
    st.error("No data available from stable sources")
    st.stop()

# ================= SONG LIST =================
songs = df["song"].dropna().unique().tolist()

selected = st.selectbox("🎵 Select song", songs)

# ================= MATCH ENGINE (ROBUST) =================
def match(df, song):
    song = norm(song)
    return df[df["song"].fillna("").apply(lambda x: song in x)]

filtered = match(df, selected)

# ================= SCORE ENGINE =================
def score(df):
    if df.empty:
        return 0

    pos = df["position"].dropna()

    base = (100 - pos).sum() if len(pos) else 0
    boost = len(df) * 5  # presencia global

    return base + boost

total_score = score(filtered)

# ================= SAFE METRICS =================
pos = filtered["position"].dropna()

best = int(pos.min()) if len(pos) else 0
top10 = int((pos <= 10).sum()) if len(pos) else 0
avg = round(pos.mean(), 1) if len(pos) else 0

# ================= UI =================
st.title("🔥 BM GLOBAL TRACKER")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best Position", best)
c2.metric("🔥 Top 10 Entries", top10)
c3.metric("📊 Avg Position", avg)
c4.metric("🌐 Global Score", int(total_score))

st.markdown("---")

tab1, tab2 = st.tabs(["📊 Data", "📈 Analytics"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    if filtered.empty:
        st.info("No chart data for this selection")
    else:
        fig = px.bar(filtered, x="platform", y="position", color="country",
                     title="Global Chart Presence", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# ================= INSIGHT =================
st.markdown("### 🧠 Insight Engine")

if total_score > 80:
    st.success("🔥 Strong global performance")
elif total_score > 30:
    st.info("📈 Moderate global presence")
else:
    st.warning("📊 Emerging track")

# ================= OPTIONAL REFRESH =================
if st.sidebar.toggle("Auto refresh"):
    st.rerun()
