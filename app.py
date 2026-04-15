import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import os
import time
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER CHARTS", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- ESTILO PRO ----------------
st.markdown("""
<style>
.main {
    background-color: #0d1117;
}
h1 {
    color: #ff4b4b;
    text-align: center;
}
.stMetric {
    background-color: #161b22;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HISTORIAL YOUTUBE ----------------
def save_youtube_history(df):
    if df.empty:
        return

    df_copy = df.copy()
    df_copy["timestamp"] = datetime.now()

    file = "yt_history.csv"

    if not os.path.exists(file):
        df_copy.to_csv(file, index=False)
    else:
        df_copy.to_csv(file, mode="a", header=False, index=False)

def load_youtube_history():
    file = "yt_history.csv"

    if os.path.exists(file):
        df = pd.read_csv(file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    return pd.DataFrame()

# ---------------- ITUNES ----------------
@st.cache_data(ttl=300)
def fetch_itunes():
    url = "https://kworb.net/itunes/artist/babymonster.html"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")

            for row in rows[1:]:
                cols = row.find_all("td")

                if len(cols) >= 3:
                    song = cols[0].text.strip()
                    country = cols[1].text.strip()
                    pos = cols[2].text.strip()

                    if song and len(song) > 2:
                        data.append({
                            "Canción": song,
                            "País": country,
                            "Posición": pos,
                            "Plataforma": "iTunes/Apple Music"
                        })

        df = pd.DataFrame(data)

        if not
