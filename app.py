import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="BM Global Tracker", layout="wide")
DB = "bm_dataset.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM data", conn)
    conn.close()
    return df

# ================= INIT =================
init_db()

# ================= SIDEBAR =================
st.sidebar.title("⚙️ Data Control")

# -------- CSV UPLOAD --------
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file)
        df_upload.columns = [c.lower().strip() for c in df_upload.columns]

        if not all(col in df_upload.columns for col in ["song","platform","country"]):
            st.sidebar.error("CSV must include: song, platform, country")
        else:
            df_upload["clean_song"] = df_upload["song"].astype(str).str.lower().str.strip()
            df_upload["position"] = pd.to_numeric(df_upload.get("position"), errors="coerce")
            df_upload["views"] = pd.to_numeric(df_upload.get("views"), errors="coerce")
            df_upload["timestamp"] = datetime.now().isoformat()

            conn = sqlite3.connect(DB)
            df_upload.to_sql("data", conn, if_exists="append", index=False)
            conn.close()

            st.sidebar.success("✅ Data uploaded")

    except:
        st.sidebar.error("Error uploading CSV")

# -------- MANUAL INPUT --------
st.sidebar.markdown("## ➕ Add Data")

new_song = st.sidebar.text_input("Song")
new_platform = st.sidebar.selectbox("Platform", ["itunes", "youtube"])
new_country = st.sidebar.text_input("Country")
new_position = st.sidebar.text_input("Position")
new_views = st.sidebar.text_input("Views")

if st.sidebar.button("Add Data"):
    try:
        pos = int(new_position) if new_position else None
    except:
        pos = None

    try:
        views = int(new_views) if new_views else None
    except:
        views = None

    conn = sqlite3.connect(DB)

    df_new = pd.DataFrame([{
        "song": new_song,
        "clean_song": new_song.lower().strip(),
        "platform": new_platform,
        "country": new_country,
        "position": pos,
        "views": views,
        "timestamp": datetime.now().isoformat()
    }])

    df_new.to_sql("data", conn, if_exists="append", index=False)
    conn.close()

    st.sidebar.success("✅ Added")

# ================= LOAD =================
df = load_data()

if df.empty:
    st.warning("No data available")
    st.stop()

# ================= GLOBAL RANKING ENGINE =================
grouped = df.groupby("clean_song").agg({
    "position": lambda x: (100 - x.dropna()).sum(),
    "views": "sum"
}).reset_index()

grouped["score"] = grouped["position"].fillna(0) + (grouped["views"].fillna(0) / 1_000_000)

ranking = grouped.sort_values("score", ascending=False).reset_index(drop=True)
ranking["rank"] = ranking.index + 1

# ================= UI =================
st.title("🔥 BM GLOBAL TRACKER")

# ================= TOP CHART =================
st.subheader("🏆 Global Top Charts")

top10 = ranking.head(10)

fig = px.bar(
    top10,
    x="score",
    y="clean_song",
    orientation="h",
    title="Top 10 Songs",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(top10, use_container_width=True)

st.markdown("---")

# ================= SELECT SONG =================
selected = st.selectbox("🎵 Select song", ranking["clean_song"])

filtered = df[df["clean_song"] == selected]

# ================= METRICS =================
pos = filtered["position"].dropna()
views = filtered["views"].fillna(0)

best = int(pos.min()) if len(pos) else 0
top10_count = int((pos <= 10).sum()) if len(pos) else 0
total_views = int(views.sum())

score = ranking[ranking["clean_song"] == selected]["score"].values[0]

# ================= METRIC CARDS =================
c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Best Position", best)
c2.metric("🔥 Top 10 Entries", top10_count)
c3.metric("👁️ Views", total_views)
c4.metric("🌐 Score", int(score))

# ================= DETAIL TABS =================
tab1, tab2 = st.tabs(["📊 Data", "📈 Charts"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    fig = px.bar(
        filtered,
        x="platform",
        y="views",
        color="platform",
        title="Platform Breakdown",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= INSIGHT =================
st.markdown("### 🧠 Insight")

if score > 150:
    st.success("🔥 GLOBAL DOMINATION")
elif score > 80:
    st.info("📈 STRONG HIT")
else:
    st.warning("📊 DEVELOPING")
