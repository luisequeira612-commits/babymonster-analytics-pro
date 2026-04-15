import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

BASE_URL = "https://kworb.net"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- SCRAPER GLOBAL ----------------
@st.cache_data(ttl=300)
def fetch_all_data():
    url = f"{BASE_URL}/itunes/artist/babymonster.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows[1:]:
                cols = row.find_all("td")

                # necesitamos al menos 3 columnas: canción, país, posición
                if len(cols) >= 3:
                    song = cols[0].text.strip()
                    country = cols[1].text.strip()
                    pos = cols[2].text.strip()

                    # FILTROS
                    if (
                        song
                        and len(song) > 2
                        and not song.isdigit()
                        and "total" not in song.lower()
                        and "worldwide" not in song.lower()
                    ):
                        data.append({
                            "Canción": song,
                            "País": country,
                            "Posición": pos
                        })

        df = pd.DataFrame(data)

        if not df.empty:
            df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

        return df

    except:
        return pd.DataFrame()

# ---------------- UI ----------------
st.title("🚀 BABYMONSTER CHARTS")

st.write("Sistema global de charts por canción")

df = fetch_all_data()

if df.empty:
    st.error("No se pudieron cargar datos desde kworb")
    st.stop()

# ---------------- SELECTOR ----------------
songs = sorted(df["Canción"].dropna().unique())

selected_song = st.selectbox("🎵 Selecciona canción", songs)

# ---------------- FILTRAR ----------------
filtered = df[df["Canción"] == selected_song]

# ---------------- RESULTADOS ----------------
st.subheader(f"🌍 Charts - {selected_song}")

col1, col2 = st.columns([2,1])

with col1:
    st.dataframe(filtered, use_container_width=True)

with col2:
    top1 = (filtered["Posición"] == 1).sum()
    top10 = (filtered["Posición"] <= 10).sum()
    avg = filtered["Posición"].mean()

    st.metric("🥇 #1 Países", top1)
    st.metric("🔥 Top 10", top10)
    st.metric("📊 Promedio", round(avg,1) if not pd.isna(avg) else 0)

# ---------------- MAPA ----------------
st.subheader("📍 Mapa Global")

try:
    fig = px.choropleth(
        filtered,
        locations="País",
        locationmode="country names",
        color="Posición",
        color_continuous_scale="Reds_r",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

except:
    st.warning("No se pudo generar el mapa")

# ---------------- INSIGHT ----------------
st.subheader("🧠 Insight")

if not filtered.empty:
    avg = filtered["Posición"].mean()

    if avg < 20:
        st.success("🔥 HIT GLOBAL")
    elif avg < 50:
        st.info("Buen rendimiento")
    else:
        st.warning("Impacto moderado")

# ---------------- DEBUG ----------------
with st.expander("⚙️ Ver datos completos"):
    st.dataframe(df)
