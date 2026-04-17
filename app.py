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

def insert_sample_data():
    conn = sqlite3.connect(DB)

    # 👉 dataset inicial (puedes editar esto)
    sample = pd.DataFrame([
        {"song":"DRIP","clean_song":"drip","platform":"itunes","country":"japan","position":3,"views":None},
        {"song":"DRIP","clean_song":"drip","platform":"itunes","country":"usa","position":8,"views":None},
        {"song":"DRIP MV","clean_song":"drip","platform":"youtube","country":"global","position":None,"views":52000000},

        {"song":"SHEESH","clean_song":"sheesh","platform":"itunes","country":"korea","position":2,"views":None},
        {"song":"SHEESH MV","clean_song":"sheesh","platform":"youtube","country":"global","position":None,"views":120000000},

        {"song":"BATTER UP","clean_song":"batter up","platform":"itunes","country":"global","position":10,"views":None},
        {"song":"BATTER UP MV","clean_song":"batter up","platform":"youtube","country":"global","position":None,"views":300000000},
    ])

    sample["timestamp"] = datetime.now().isoformat()

    sample.to_sql("data", conn, if_exists="append", index=False)
    conn.close()

def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM data", conn)
    conn.close()
    return df

# ================= INIT =================
init_db()

# botón para poblar dataset (solo una vez)
if st.sidebar.button("⚡ Load Sample Data"):
    insert_sample_data()
    st.success("Sample data loaded")

df = load_data()

if df.empty:
    st.warning("No data yet. Click 'Load Sample Data'")
    st.stop()

# ================= SONGS =================
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
c3.metric("👁️ Views", total_views)
c4.metric("🌐 Score", int(score))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Data", "📈 Charts", "🕒 History"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

with tab2:
    fig = px.bar(filtered,
                 x="platform",
                 y="views",
                 color="platform",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    grouped = df.groupby("timestamp")["views"].sum().reset_index()

    fig = px.line(grouped,
                  x="timestamp",
                  y="views",
                  title="Growth Over Time",
                  template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

# ================= INSIGHT =================
st.markdown("### 🧠 Insight")

if score > 100:
    st.success("🔥 GLOBAL HIT")
elif score > 50:
    st.info("📈 STRONG PERFORMANCE")
else:
    st.warning("📊 GROWING TRACK")
