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
st.sidebar.markdown("## 📂 Upload CSV")

uploaded_file = st.sidebar.file_uploader("Upload your data", type=["csv"])

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file)

        df_upload.columns = [c.lower().strip() for c in df_upload.columns]

        required = ["song", "platform", "country"]

        if not all(col in df_upload.columns for col in required):
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
st.sidebar.markdown("## ➕ Add Data Manually")

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

    st.sidebar.success("✅ Data added")

# ================= LOAD DATA =================
df = load_data()

if df.empty:
    st.warning("No data available. Upload CSV or add manually.")
    st.stop()

# ================= SELECT SONG =================
songs = sorted(df["clean_song"].unique())
selected = st.selectbox("🎵 Select song", songs)

filtered = df[df["clean_song"] == selected]

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
c1.metric("🏆 Best Position", best)
c2.metric("🔥 Top 10", top10)
c3.metric("👁️ Total Views", total_views)
c4.metric("🌐 Score", int(score))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Data", "📈 Charts", "🕒 History"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    fig = px.bar(
        filtered,
        x="platform",
        y="views",
        color="platform",
        title="Platform Performance",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    grouped = df.groupby("timestamp")["views"].sum().reset_index()

    fig = px.line(
        grouped,
        x="timestamp",
        y="views",
        title="Growth Over Time",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= INSIGHT =================
st.markdown("### 🧠 Insight")

if score > 100:
    st.success("🔥 GLOBAL HIT")
elif score > 50:
    st.info("📈 STRONG PERFORMANCE")
else:
    st.warning("📊 GROWING TRACK")
