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

init_db()

# ================= SIDEBAR =================
st.sidebar.title("⚙️ Data Control")

# -------- CSV UPLOAD --------
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file)
        df_upload.columns = [c.lower().strip() for c in df_upload.columns]

        if not all(col in df_upload.columns for col in ["song","platform","country","position"]):
            st.sidebar.error("CSV must include: song, platform, country, position")
        else:
            df_upload["clean_song"] = df_upload["song"].astype(str).str.lower().str.strip()
            df_upload["position"] = pd.to_numeric(df_upload["position"], errors="coerce")
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
new_platform = st.sidebar.selectbox("Platform", [
    "itunes_song_global",
    "itunes_album_global",
    "itunes_song_europe",
    "itunes_album_europe",
    "apple_music_global",
    "apple_music_country",
    "spotify",
    "youtube_trending"
])
new_country = st.sidebar.text_input("Country")
new_position = st.sidebar.text_input("Position")

if st.sidebar.button("Add Data"):
    try:
        pos = int(new_position)
    except:
        pos = None

    conn = sqlite3.connect(DB)

    df_new = pd.DataFrame([{
        "song": new_song,
        "clean_song": new_song.lower().strip(),
        "platform": new_platform,
        "country": new_country,
        "position": pos,
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

# ================= PREP =================
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

# ================= EVOLUTION ENGINE =================
latest = df.groupby("clean_song").tail(1)
previous = df.groupby("clean_song").nth(-2).reset_index()

ranking = latest.merge(
    previous[["clean_song","position"]],
    on="clean_song",
    how="left",
    suffixes=("_latest", "_prev")
)

# peak histórico
peak = df.groupby("clean_song")["position"].min().reset_index()
peak.columns = ["clean_song","peak"]

ranking = ranking.merge(peak, on="clean_song", how="left")

# change
def get_change(row):
    if pd.isna(row["position_prev"]):
        return "NEW"

    if pd.isna(row["position_latest"]):
        return "-"

    diff = row["position_prev"] - row["position_latest"]

    if diff > 0:
        return f"↑ {diff}"
    elif diff < 0:
        return f"↓ {abs(diff)}"
    else:
        return "—"

ranking["change"] = ranking.apply(get_change, axis=1)

# status
def get_status(change):
    if change == "NEW":
        return "🆕 NEW"
    if "↑" in change:
        return "🔼 UP"
    if "↓" in change:
        return "🔽 DOWN"
    return "➖ SAME"

ranking["status"] = ranking["change"].apply(get_status)

ranking = ranking.sort_values("position_latest")
ranking["rank"] = range(1, len(ranking)+1)

# ================= UI =================
st.title("🔥 BM GLOBAL TRACKER")

st.subheader("🏆 Global Chart")

display = ranking[[
    "rank",
    "clean_song",
    "position_latest",
    "change",
    "peak",
    "status"
]].rename(columns={
    "clean_song":"Song",
    "position_latest":"Position",
    "change":"Change",
    "peak":"Peak",
    "status":"Status"
})

st.dataframe(display, use_container_width=True)

# ================= TOP 10 =================
st.subheader("📊 Top 10")

fig = px.bar(
    ranking.head(10),
    x="position_latest",
    y="clean_song",
    orientation="h",
    template="plotly_dark"
)

fig.update_layout(yaxis={'categoryorder':'total ascending'})

st.plotly_chart(fig, use_container_width=True)

# ================= SELECT SONG =================
selected = st.selectbox("🎵 Select song", ranking["clean_song"])

song_df = df[df["clean_song"] == selected]

# ================= HISTORY =================
st.subheader("📈 Song History")

history = song_df.groupby("timestamp")["position"].mean().reset_index()

fig = px.line(
    history,
    x="timestamp",
    y="position",
    markers=True,
    template="plotly_dark"
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

# ================= METRICS =================
st.subheader("📊 Song Stats")

best = int(song_df["position"].min()) if not song_df["position"].dropna().empty else 0
entries = len(song_df)
top10 = (song_df["position"] <= 10).sum()

c1, c2, c3 = st.columns(3)

c1.metric("🏆 Peak", best)
c2.metric("🔥 Top 10", int(top10))
c3.metric("📊 Entries", int(entries))
