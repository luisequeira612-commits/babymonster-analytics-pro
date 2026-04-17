import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time
import re
import difflib

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# ================= UTILS =================
def norm(x):
    return " ".join(str(x).lower().split())

def safe_int(x):
    try:
        nums = re.findall(r'\d+', str(x))
        return int(nums[0]) if nums else None
    except:
        return None

def empty_df():
    return pd.DataFrame(columns=["song","country","position","platform"])

# ================= CORE SCRAPER =================
@st.cache_data(ttl=300)
def fetch_global_data():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        # Usamos un timeout para que no se quede colgado
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            st.error(f"Error de conexión: Código {response.status_code}")
            return empty_df()

        soup = BeautifulSoup(response.text, "lxml")
        data = []

        # Buscamos la sección de las columnas blancas (p_container)
        containers = soup.find_all("div", class_="p_container")

        if not containers:
            # Plan B: Si Kworb cambió el nombre de la clase
            st.warning("No se encontraron los contenedores estándar. Reintentando con Plan B...")
            return empty_df()

        for container in containers:
            all_text = container.get_text(separator="\n").split("\n")
            # El nombre de la canción suele ser el primer texto no vacío
            song_name_list = [t.strip() for t in all_text if t.strip() and "spotify" not in t.lower() and "itunes" not in t.lower() and "apple" not in t.lower()]
            
            if not song_name_list: continue
            song_name = norm(song_name_list[0])

            current_platform = "unknown"
            for line in all_text:
                l = line.strip().lower()
                if not l: continue
                
                if "spotify:" in l: current_platform = "spotify"
                elif "itunes:" in l: current_platform = "itunes"
                elif "apple music:" in l: current_platform = "apple_music"
                
                if "#" in l:
                    parts = line.strip().split(" ")
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
    except Exception as e:
        st.error(f"Error detallado: {e}")
        return empty_df()

@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        url = "https://kworb.net/youtube/trending.html"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
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

df = fetch_global_data()
yt = fetch_youtube()

if df.empty:
    st.info("🔄 Los datos se están resistiendo. Pulsa 'Forzar Actualización' en el sidebar.")
    if st.sidebar.button("♻️ Forzar Actualización"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# --- SELECTOR ---
songs = sorted(df["song"].unique().tolist())
selected = st.selectbox("🎵 Selecciona una canción", songs)

# --- FUZZY MATCH ---
def match(name, target_df):
    if target_df.empty: return target_df
    candidates = target_df["song"].unique()
    m = difflib.get_close_matches(norm(name), candidates, n=1, cutoff=0.3)
    return target_df[target_df["song"] == m[0]] if m else target_df.iloc[0:0]

filtered = match(selected, df)
yt_filtered = match(selected, yt)

# --- SCORE & METRICS ---
def get_score(f, y):
    pts = (150 - f["position"].fillna(150)).sum() if not f.empty else 0
    v = (y["views"].sum() / 1_000_000) if not y.empty else 0
    return pts + v

pos = filtered["position"].dropna()
c1, c2, c3, c4 = st.columns(4)
c1.metric("🏆 Best Rank", int(pos.min()) if not pos.empty else 0)
c2.metric("🔥 Total Charts", len(filtered))
c3.metric("📊 Average", round(pos.mean(), 1) if not pos.empty else 0)
c4.metric("🌐 Global Score", int(get_score(filtered, yt_filtered)))

st.markdown("---")

# --- TABS ---
t1, t2, t3 = st.tabs(["📊 Desglose", "🎥 YouTube", "🏆 Ranking"])

with t1:
    st.dataframe(filtered.sort_values("position"), use_container_width=True)

with t2:
    if yt_filtered.empty: st.write("No hay tendencias en YT ahora.")
    else: st.metric("Views (Trending)", f"{yt_filtered['views'].sum():,}"); st.table(yt_filtered)

with t3:
    all_r = [{"song": s.upper(), "score": get_score(match(s, df), match(s, yt))} for s in songs]
    rdf = pd.DataFrame(all_r).sort_values("score", ascending=False)
    st.dataframe(rdf, use_container_width=True)
    st.plotly_chart(px.bar(rdf.head(10), x="song", y="score", color="score", color_continuous_scale="Reds", template="plotly_dark"))

if st.sidebar.button("♻️ Limpiar Caché"):
    st.cache_data.clear()
    st.rerun()
