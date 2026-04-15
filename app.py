import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER GLOBAL CHART", layout="wide")

BASE_URL = "https://kworb.net"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- OBTENER CANCIONES (ROBUSTO) ----------------
@st.cache_data(ttl=600)
def get_song_list():
    url = f"{BASE_URL}/itunes/artist/babymonster.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return {}

        soup = BeautifulSoup(res.text, "lxml")
        songs = {}

        # 1. Intentar detectar links reales
        for a in soup.find_all("a", href=True):
            href = a["href"]
            name = a.text.strip()

            if "song" in href and name:
                songs[name] = urljoin(BASE_URL, href)

        # 2. Fallback (si no hay links)
        if not songs:
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows[1:]:
                    cols = row.find_all("td")

                    if cols:
                        name = cols[0].text.strip()

                        if name and len(name) > 1 and not name.isdigit():
                            songs[name] = None

        # 3. Agregar CHOOM placeholder si no existe
        if not any("choom" in s.lower() for s in songs.keys()):
            songs = {"CHOOM (PRE-DEBUT)": None} | songs

        return songs

    except:
        return {}

# ---------------- SCRAPEAR CANCIÓN ----------------
@st.cache_data(ttl=300)
def scrape_song(song_url):
    if not song_url:
        return pd.DataFrame()

    try:
        res = requests.get(song_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows[1:]:
                cols = row.find_all("td")

                if len(cols) >= 2:
                    country = cols[0].text.strip()
                    pos = cols[1].text.strip()

                    data.append({
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
st.title("🚀 BABYMONSTER GLOBAL CHART")

st.write("Selecciona una canción para ver su rendimiento global:")

songs = get_song_list()

if not songs:
    st.error("⚠️ No se pudieron cargar canciones desde kworb")
    st.stop()

song_names = list(songs.keys())

selected_song = st.selectbox("🎵 Canción", song_names)

song_url = songs[selected_song]

# ---------------- PRE-DEBUT ----------------
if "CHOOM" in selected_song:
    st.warning("⏳ 'CHOOM' aún no tiene datos en charts")
    st.info("La app detectará automáticamente cuando debute en charts")
    st.stop()

# ---------------- SIN LINK ----------------
if song_url is None:
    st.warning("⚠️ Esta canción no tiene página individual en kworb")
    st.stop()

st.markdown(f"🔗 Fuente: {song_url}")

# ---------------- SCRAPING ----------------
df = scrape_song(song_url)

# ---------------- RESULTADOS ----------------
if not df.empty:
    st.subheader(f"🌍 Charts Globales - {selected_song}")

    col1, col2 = st.columns([2,1])

    with col1:
        st.dataframe(df, use_container_width=True)

    with col2:
        top1 = (df["Posición"] == 1).sum()
        top10 = (df["Posición"] <= 10).sum()
        avg = df["Posición"].mean()

        st.metric("🥇 #1 Países", top1)
        st.metric("🔥 Top 10", top10)
        st.metric("📊 Promedio", round(avg,1) if not pd.isna(avg) else 0)

    # -------- MAPA --------
    st.subheader("📍 Mapa Global")

    try:
        fig = px.choropleth(
            df,
            locations="País",
            locationmode="country names",
            color="Posición",
            color_continuous_scale="Reds_r",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

    except:
        st.warning("No se pudo generar el mapa")

else:
    st.warning("No hay datos disponibles para esta canción")

# ---------------- INSIGHT ----------------
if not df.empty:
    st.subheader("🧠 Insight")

    avg = df["Posición"].mean()

    if avg < 20:
        st.success("🔥 HIT GLOBAL FUERTE")
    elif avg < 50:
        st.info("Buen rendimiento internacional")
    else:
        st.warning("Impacto moderado")

# ---------------- DEBUG ----------------
with st.expander("⚙️ Ver canciones detectadas"):
    st.write(song_names)
