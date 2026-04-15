import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.set_page_config(page_title="BABYMONSTER SONG TRACKER", layout="wide")

BASE_URL = "https://kworb.net"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- OBTENER CANCIONES ----------------
@st.cache_data(ttl=600)
def get_song_list():
    url = f"{BASE_URL}/itunes/artist/babymonster.html"
    res = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(res.text, "lxml")

    songs = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/song/" in href:
            full_url = urljoin(BASE_URL, href)
            name = a.text.strip()

            if name and name not in songs:
                songs[name] = full_url

    return songs

# ---------------- SCRAPEAR CANCIÓN ----------------
@st.cache_data(ttl=300)
def scrape_song(song_url):
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

    # limpiar números
    df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")

    return df

# ---------------- UI ----------------
st.title("🚀 BABYMONSTER MINI KWORB")

st.write("Selecciona una canción para ver su performance global:")

songs = get_song_list()

if not songs:
    st.error("No se pudieron cargar canciones")
    st.stop()

song_names = list(songs.keys())

selected_song = st.selectbox("🎵 Canción", song_names)

song_url = songs[selected_song]

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
        st.metric("📊 Promedio", round(avg,1))

    # -------- MAPA --------
    st.subheader("📍 Mapa Global")

    map_df = df.copy()

    fig = None
    try:
        import plotly.express as px

        fig = px.choropleth(
            map_df,
            locations="País",
            locationmode="country names",
            color="Posición",
            color_continuous_scale="Reds_r",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Mapa no disponible")

else:
    st.warning("No hay datos para esta canción")

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

# ---------------- DEBUG OPCIONAL ----------------
with st.expander("⚙️ Ver canciones detectadas"):
    st.write(song_names)
