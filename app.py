import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time
import difflib

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= UTILS =================
def norm(x):
    return " ".join(str(x).lower().split())

def safe_int(x):
    try:
        # Extrae solo los números de una cadena (ej: "#122 (NE)" -> 122)
        import re
        nums = re.findall(r'\d+', str(x))
        return int(nums[0]) if nums else None
    except:
        return None

def empty_df():
    return pd.DataFrame(columns=["song","country","position","platform"])

# ================= FUZZY MATCH ENGINE =================
def best_match(song, df):
    if df.empty or "song" not in df.columns:
        return df
    song = norm(song)
    candidates = df["song"].dropna().unique()
    match = difflib.get_close_matches(song, candidates, n=1, cutoff=0.3)
    if not match:
        return df.iloc[0:0]
    return df[df["song"] == match[0]]

# ================= CORE SCRAPER (KWORB CONSOLE) =================
@st.cache_data(ttl=300)
def fetch_global_data():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "lxml")
        data = []

        # Buscamos los contenedores de cada canción (las columnas blancas)
        containers = soup.find_all("div", class_="p_container")

        for container in containers:
            # El nombre de la canción es el primer elemento de texto
            raw_text = container.get_text(separator="\n").split("\n")
            song_name = norm(raw_text[0])
            
            if not song_name or song_name == "artist": continue

            current_platform = "unknown"
            
            for line in raw_text:
                line_clean = line.strip()
                if not line_clean: continue
                
                # Detectar plataforma
                l_lower = line_clean.lower()
                if "spotify:" in l_lower: current_platform = "spotify"
                elif "itunes:" in l_lower: current_platform = "itunes"
                elif "apple music:" in l_lower: current_platform = "apple_music"
                
                # Si la línea tiene un puesto (#)
                if "#" in line_clean:
                    # Formato esperado: "#123 Country Name"
                    parts = line_clean.split(" ")
                    pos = safe_int(parts[0])
                    country = norm(" ".join(parts[1:]))
                    
                    if pos:
                        data.append({
                            "song": song_name,
                            "country": country,
                            "position": pos,
                            "platform": current_platform
                        })

        return pd.DataFrame(data)
    except:
        return empty_df()

@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "lxml")
        data = []
        for row in soup.find_all("tr"):
            c = row.find_all("td")
            if len(c) >= 5:
                title = norm(c[2].text)
                if "babymonster" in title:
                    data.append({"song": title, "views": safe_int(c[3].text)})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["song","views"])

# ================= APP LOGIC =================
st.title("🔥 BABYMONSTER CHARTS")

# Cargar datos
df = fetch_global_data()
yt = fetch_youtube()

if df.empty:
    st.error("No se pudieron cargar los datos. Intenta limpiar el caché.")
    st.stop()

# Selector de canción
songs = sorted(df["song"].unique().tolist())
selected = st.selectbox("🎵 Selecciona una canción", songs)

# Filtrado Inteligente
filtered = best_match(selected, df)
yt_filtered = best_match(selected, yt)

# Cálculo de Score
def get_score(f_df, y_df):
    pts = (150 - f_df["position"].fillna(150)).sum() if not f_df.empty else 0
    v_pts = (y_df["views"].sum() / 1_000_000) if not y_df.empty else 0
    return pts + v_pts

# Métricas
pos = filtered["position"].dropna()
c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best Rank", int(pos.min()) if not pos.empty else 0)
c2.metric("🔥 Total Entries", len(filtered))
c3.metric("📊 Average", round(pos.mean(), 1) if not pos.empty else 0)
c4.metric("🌐 Global Score", int(get_score(filtered, yt_filtered)))

st.markdown("---")

# Tabs de visualización
tab1, tab2, tab3 = st.tabs(["📊 Desglose por País", "🎥 YouTube Status", "🏆 Ranking General"])

with tab1:
    # Mostrar tabla limpia
    display_df = filtered.copy()
    display_df = display_df.sort_values("position")
    st.dataframe(display_df[["platform", "country", "position"]], use_container_width=True)

with tab2:
    if yt_filtered.empty:
        st.info("No se encontraron tendencias actuales en YouTube para esta canción.")
    else:
        st.write(f"### {selected.upper()}")
        st.metric("Views (Trending Section)", f"{yt_filtered['views'].sum():,}")
        st.dataframe(yt_filtered)

with tab3:
    all_ranks = []
    for s in songs:
        f = best_match(s, df)
        y = best_match(s, yt)
        all_ranks.append({"song": s.upper(), "score": get_score(f, y)})
    
    rank_df = pd.DataFrame(all_ranks).sort_values("score", ascending=False)
    st.subheader("Top Performers")
    st.dataframe(rank_df, use_container_width=True)
    
    fig = px.bar(rank_df.head(10), x="song", y="score", 
                 color="score", color_continuous_scale="Reds",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# Sidebar
st.sidebar.header("Opciones")
if st.sidebar.button("♻️ Forzar Actualización"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.info("Datos obtenidos en tiempo real de Kworb Global Console.")
