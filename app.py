import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px
import time
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER CHART GLOBAL", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
.stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
h1, h2, h3 { color: #ff4b4b; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ---------------- UTILIDADES ----------------
def normalize_countries(df):
    country_map = {
        "USA": "United States",
        "UK": "United Kingdom",
        "Korea": "South Korea"
    }
    df["País"] = df["País"].replace(country_map)
    return df

def save_history(df):
    if not df.empty:
        df["timestamp"] = datetime.now()
        file = "history_itunes.csv"
        if not os.path.exists(file):
            df.to_csv(file, index=False)
        else:
            df.to_csv(file, mode="a", header=False, index=False)

# ---------------- SCRAPER ----------------
@st.cache_data(ttl=300)
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    itunes_df, am_df, yt_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    global_tabs = {"WW Songs": [], "WW Albums": [], "EU Songs": [], "EU Albums": []}
    error = None

    try:
        r = requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            headers_row = [th.text.lower() for th in rows[0].find_all(["th", "td"])]

            # ---- GLOBAL TABLES ----
            if "worldwide" in headers_row:
                prev_text = ""
                if table.previous_sibling:
                    prev_text = str(table.previous_sibling).lower()

                is_album = "album" in table.get("id", "").lower() or "album" in prev_text

                for row in rows[1:11]:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        name = cols[0].text.strip()[:30]
                        ww = cols[1].text.strip()
                        eu = cols[2].text.strip()

                        if is_album:
                            global_tabs["WW Albums"].append({"Album": name, "Rank": ww})
                            global_tabs["EU Albums"].append({"Album": name, "Rank": eu})
                        else:
                            global_tabs["WW Songs"].append({"Song": name, "Rank": ww})
                            global_tabs["EU Songs"].append({"Song": name, "Rank": eu})

            # ---- ITUNES / AM ----
            elif "country" in headers_row or "pos" in headers_row:
                is_am = "applemusic" in table.get("id", "").lower()
                data_list = []

                for row in rows[1:101]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        data_list.append({
                            "País": cols[0].text.strip(),
                            "Pos": cols[1].text.strip()
                        })

                df_temp = pd.DataFrame(data_list)

                if is_am:
                    am_df = df_temp
                else:
                    itunes_df = df_temp

        # ---- YOUTUBE ----
        r_yt = requests.get("https://kworb.net/youtube/trending.html", headers=headers, timeout=10)
        soup_yt = BeautifulSoup(r_yt.text, "lxml")

        yt_list = []
        for row in soup_yt.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 4:
                title = cols[2].text.lower()
                if "babymonster" in title:
                    yt_list.append({
                        "Video": cols[2].text.strip(),
                        "Trending": cols[3].text.strip()
                    })

        yt_df = pd.DataFrame(yt_list)

    except Exception as e:
        error = str(e)

    return itunes_df, am_df, yt_df, global_tabs, error

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📊 MONITOR")
    st.write("**Analyst:** Luis Sequeira")

    auto = st.toggle("Auto Refresh (60s)")

    release_date = datetime(2026, 5, 4)
    delta = release_date - datetime.now()
    st.metric("Días para 'Choom'", f"{max(0, delta.days)}d {max(0, delta.seconds // 3600)}h")

    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()

# ---------------- MAIN ----------------
st.title("🚀 BABYMONSTER CHART GLOBAL")

df_itunes, df_am, df_yt, global_tabs, error = fetch_data()

# ---- ERROR ----
if error:
    st.warning("⚠️ Problema obteniendo datos (kworb puede haber cambiado estructura)")

# ---- NORMALIZAR ----
if not df_itunes.empty:
    df_itunes = normalize_countries(df_itunes)

# ---- HISTORIAL ----
save_history(df_itunes)

# ---- SCORE ----
def calculate_score(df):
    try:
        df["Pos"] = pd.to_numeric(df["Pos"], errors="coerce")
        top10 = (df["Pos"] <= 10).sum()
        top1 = (df["Pos"] == 1).sum()
        return top10 * 2 + top1 * 5
    except:
        return 0

score = calculate_score(df_itunes)

st.metric("🔥 GLOBAL SCORE", score)

# ---- ALERTAS ----
if not df_itunes.empty:
    if (df_itunes["Pos"] == "1").any():
        st.success("🚨 #1 DETECTADO EN ITUNES")

    if df_itunes["Pos"].astype(float).mean() < 20:
        st.info("🔥 FUERTE DOMINIO GLOBAL")

# ---- TABS ----
st.subheader("🌎 GLOBAL BREAKDOWN")
t1, t2, t3, t4 = st.tabs(["🎵 WW Songs", "💿 WW Albums", "🇪🇺 EU Songs", "📀 EU Albums"])

with t1:
    st.dataframe(pd.DataFrame(global_tabs["WW Songs"]), use_container_width=True)
with t2:
    st.dataframe(pd.DataFrame(global_tabs["WW Albums"]), use_container_width=True)
with t3:
    st.dataframe(pd.DataFrame(global_tabs["EU Songs"]), use_container_width=True)
with t4:
    st.dataframe(pd.DataFrame(global_tabs["EU Albums"]), use_container_width=True)

# ---- MAPA ----
if not df_itunes.empty:
    st.subheader("📍 MAPA GLOBAL")
    df_itunes["Pos"] = pd.to_numeric(df_itunes["Pos"], errors="coerce")

    fig = px.choropleth(
        df_itunes,
        locations="País",
        locationmode="country names",
        color="Pos",
        color_continuous_scale="Reds_r",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---- COLUMNAS ----
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🍎 iTunes")
    st.dataframe(df_itunes, use_container_width=True, height=400)

with col2:
    st.subheader("🎵 Apple Music")
    st.dataframe(df_am, use_container_width=True, height=400)

with col3:
    st.subheader("🔥 YouTube")
    if not df_yt.empty:
        for _, row in df_yt.iterrows():
            with st.expander(row["Video"][:30]):
                st.write(f"Tendencia: {row['Trending']}")
    else:
        st.write("Sin datos")

# ---- INSIGHT ----
if not df_itunes.empty:
    avg = df_itunes["Pos"].mean()
    st.subheader("🧠 Insight automático")

    if avg < 10:
        st.write("Dominio global extremo 🔥")
    elif avg < 30:
        st.write("Buen rendimiento global")
    else:
        st.write("Rendimiento moderado")

# ---- AUTO REFRESH ----
if auto:
    time.sleep(60)
    st.rerun()

# ---- FOOTER ----
st.markdown("<p style='text-align: center;'>© 2026 Luis Sequeira | PRO Dashboard</p>", unsafe_allow_html=True)
