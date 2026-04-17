import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

# Headers más realistas para evitar bloqueos
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def safe_int(x):
    try:
        nums = re.findall(r'\d+', str(x))
        return int(nums[0]) if nums else None
    except:
        return None

# ================= SCRAPER SIMPLIFICADO =================
@st.cache_data(ttl=300)
def fetch_all_data():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        data = []
        # Buscamos la sección principal de canciones
        containers = soup.find_all("div", class_="p_container")
        
        for container in containers:
            # Texto completo de la "cajita"
            lines = [l.strip() for l in container.get_text(separator="\n").split("\n") if l.strip()]
            if not lines: continue
            
            song_name = lines[0].lower()
            current_platform = "general"
            
            for line in lines[1:]:
                l_lower = line.lower()
                # Detectar plataforma
                if "spotify:" in l_lower: current_platform = "spotify"
                elif "itunes:" in l_lower: current_platform = "itunes"
                elif "apple music:" in l_lower: current_platform = "apple music"
                
                # Extraer posición y país
                if "#" in line:
                    parts = line.split(" ")
                    pos = safe_int(parts[0])
                    country = " ".join(parts[1:]).strip().lower()
                    if pos:
                        data.append({
                            "song": song_name,
                            "country": country,
                            "position": pos,
                            "platform": current_platform
                        })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# ================= UI =================
st.title("🔥 BABYMONSTER CHARTS")

# Botón de limpieza manual en el sidebar
if st.sidebar.button("♻️ Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

df = fetch_all_data()

if df.empty:
    st.warning("⚠️ No se pudieron obtener datos de Kworb. Intenta pulsar el botón de 'Actualizar Datos' en el sidebar.")
    st.stop()

# Selección de canción
song_list = sorted(df["song"].unique())
selected_song = st.selectbox("🎵 Selecciona una canción", song_list)

filtered = df[df["song"] == selected_song]

# Métricas rápidas
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("🏆 Mejor Puesto", int(filtered["position"].min()))
with c2:
    st.metric("📊 Países en Chart", len(filtered))
with c3:
    st.metric("🔥 Score", len(filtered) * 10) # Score simplificado

st.markdown("---")

# Visualización
tab1, tab2 = st.tabs(["📝 Lista Detallada", "📈 Resumen por Plataforma"])

with tab1:
    st.dataframe(filtered.sort_values("position"), use_container_width=True)

with tab2:
    counts = filtered["platform"].value_counts().reset_index()
    counts.columns = ["Plataforma", "Cantidad"]
    st.bar_chart(counts.set_index("Plataforma"))
    
