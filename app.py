import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import random

# ================= CONFIG =================
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

# Lista de identidades para engañar al servidor y evitar bloqueos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

def safe_int(x):
    try:
        nums = re.findall(r'\d+', str(x))
        return int(nums[0]) if nums else None
    except:
        return None

# ================= SCRAPER ROBUSTO =================
@st.cache_data(ttl=600) # Caché de 10 minutos para no saturar
def fetch_data():
    url = "https://kworb.net/itunes/artist/babymonster.html"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
        
        soup = BeautifulSoup(response.text, "html.parser")
        data = []
        
        # Buscamos los bloques de cada canción
        containers = soup.find_all("div", class_="p_container")
        
        for container in containers:
            lines = [l.strip() for l in container.get_text(separator="\n").split("\n") if l.strip()]
            if not lines: continue
            
            # La primera línea es el nombre de la canción
            song_name = lines[0].replace("Spotify:", "").replace("iTunes:", "").strip()
            platform = "General"
            
            for line in lines[1:]:
                l_low = line.lower()
                if "spotify:" in l_low: platform = "Spotify"
                elif "itunes:" in l_low: platform = "iTunes"
                elif "apple music:" in l_low: platform = "Apple Music"
                
                if "#" in line:
                    match = re.search(r'#(\d+)\s+(.+)', line)
                    if match:
                        pos = int(match.group(1))
                        country = match.group(2).strip()
                        data.append({
                            "Canción": song_name,
                            "Plataforma": platform,
                            "País": country,
                            "Posición": pos
                        })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# ================= INTERFAZ =================
st.title("🔥 BABYMONSTER CHARTS")

# Botón de emergencia en el sidebar
if st.sidebar.button("♻️ Forzar Actualización"):
    st.cache_data.clear()
    st.rerun()

df = fetch_data()

if df.empty:
    st.error("❌ El servidor de datos está saturado. Espera 1 minuto y pulsa 'Forzar Actualización'.")
    st.stop()

# Selector de canciones limpio
canciones = sorted(df["Canción"].unique())
opcion = st.selectbox("🎵 Selecciona una canción", canciones)

f_df = df[df["Canción"] == opcion].sort_values("Posición")

# Métricas
c1, c2, c3 = st.columns(3)
c1.metric("🏆 Mejor Puesto", f"#{f_df['Posición'].min()}")
c2.metric("🌍 Países", len(f_df))
c3.metric("📊 Plataformas", f_df["Plataforma"].nunique())

st.markdown("---")
st.subheader(f"Desglose Global de: {opcion}")
st.dataframe(f_df[["Plataforma", "País", "Posición"]], use_container_width=True, hide_index=True)
