import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="BM Global Tracker", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= CLEAN =================
def clean(text):
    if not text:
        return ""
    text = text.strip()
    text = text.replace("\n", " ")
    return text

def valid_song(text):
    if not text:
        return False
    t = text.lower()
    if t.startswith("#"):
        return False
    if "spotify" in t:
        return False
    if len(t) < 2:
        return False
    return True

# ================= FETCH KWORB =================
@st.cache_data(ttl=600)
def fetch_kworb():
    try:
        url = "https://kworb.net/itunes/artist/babymonster.html"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        data = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) < 3:
                continue

            # 🎯 SONG (INTELIGENTE)
            song = None

            # 1. intentar con link
            a = cols[0].find("a")
            if a:
                txt = clean(a.text)
                if valid_song(txt):
                    song = txt

            # 2. fallback texto
            if not song:
                txt = clean(cols[0].text)
                txt = txt.split("Spotify")[0]
                if valid_song(txt):
                    song = txt

            if not song:
                continue

            # 🎯 COUNTRY LIMPIO
            country_raw = clean(cols[1].text)
            country = country_raw.split("Spotify")[0].split("(")[0].strip()

            # 🎯 POSITION
            pos_raw = clean(cols[2].text)

            try:
                position = int(pos_raw)
            except:
                continue

            data.append({
                "song": song,
                "country": country,
                "position": position
            })

        df = pd.DataFrame(data)

        if df.empty:
            return df

        df["clean_song"] = df["song"].str.lower().str.strip()

        return df

    except:
        return pd.DataFrame()

# ================= LOAD =================
df = fetch_kworb()

if df.empty:
    st.warning("No data available from Kworb")
    st.stop()

# ================= KWORB STYLE AGG =================
ranking = df.groupby("clean_song").agg(
    best_position=("position", "min"),
    entries=("position", "count")
).reset_index()

ranking = ranking.sort_values(
    by=["entries","best_position"],
    ascending=[False, True]
)

ranking["rank"] = range(1, len(ranking)+1)

# ================= UI =================
st.title("BM GLOBAL TRACKER")

st.subheader("iTunes Artist Chart (Kworb Style)")

display = ranking[[
    "rank",
    "clean_song",
    "best_position",
    "entries"
]].rename(columns={
    "rank":"Pos",
    "clean_song":"Song",
    "best_position":"Peak",
    "entries":"Entries"
})

st.dataframe(display, use_container_width=True)

# ================= SELECT SONG =================
selected = st.selectbox("Select song", ranking["clean_song"])

song_df = df[df["clean_song"] == selected]

# ================= DETAIL =================
st.subheader("Chart Positions")

st.dataframe(song_df.sort_values("position"), use_container_width=True)

# ================= MAP =================
import plotly.express as px

try:
    fig = px.choropleth(
        song_df,
        locations="country",
        locationmode="country names",
        color="position",
        color_continuous_scale="Reds_r",
        title="Global iTunes Positions"
    )
    st.plotly_chart(fig, use_container_width=True)
except:
    pass
