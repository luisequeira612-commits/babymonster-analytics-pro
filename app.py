import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BABYMONSTER Global Charts", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------- STYLE PRO ----------------
st.markdown("""
<style>

/* Fondo */
.stApp {
    background-color: #0d1117;
}

/* Título */
h1 {
    text-align: center;
    color: #ff2e2e;
    font-size: 3rem;
    font-weight: 800;
}

/* Subtítulos */
h2, h3 {
    color: #ffffff;
}

/* Cards métricas */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 15px;
}

/* Tabs */
.stTabs [role="tab"] {
    color: white;
    font-weight: 600;
}

/* Dataframe */
.stDataFrame {
    border-radius: 10px;
}

/* Glow efecto */
.glow {
    text-shadow: 0 0 10px #ff2e2e;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 class='glow'>BABYMONSTER Global Charts</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Configuración")
auto = st.sidebar.toggle("Auto Refresh (60s)")

# ---------------- FETCH ----------------
@st.cache_data(ttl=300)
def fetch_itunes():
    try:
        soup = BeautifulSoup(requests.get("https://kworb.net/itunes/artist/babymonster.html", headers=HEADERS).text, "lxml")
        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                data.append({"Canción": cols[0].text.strip(),
                             "País": cols[1].text.strip(),
                             "Posición": cols[2].text.strip(),
                             "Plataforma": "iTunes"})
        df = pd.DataFrame(data)
        df["Posición"] = pd.to_numeric(df["Posición"], errors="coerce")
        return df
    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

@st.cache_data(ttl=300)
def fetch_spotify():
    try:
        soup = BeautifulSoup(requests.get("https://kworb.net/spotify/country/global_daily.html", headers=HEADERS).text, "lxml")
        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 5 and "babymonster" in cols[2].text.lower():
                data.append({"Canción": cols[1].text.strip(),
                             "País": "Global",
                             "Posición": int(cols[0].text.strip()),
                             "Plataforma": "Spotify"})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

@st.cache_data(ttl=300)
def fetch_billboard_global():
    try:
        soup = BeautifulSoup(requests.get("https://www.billboard.com/charts/billboard-global-200/", headers=HEADERS).text, "lxml")
        data = []
        for i, s in enumerate(soup.select("li ul li h3")):
            if "babymonster" in s.text.lower():
                data.append({"Canción": s.text.strip(),
                             "País": "Global",
                             "Posición": i+1,
                             "Plataforma": "BB Global 200"})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

@st.cache_data(ttl=300)
def fetch_billboard_excl():
    try:
        soup = BeautifulSoup(requests.get("https://www.billboard.com/charts/billboard-global-excl-us/", headers=HEADERS).text, "lxml")
        data = []
        for i, s in enumerate(soup.select("li ul li h3")):
            if "babymonster" in s.text.lower():
                data.append({"Canción": s.text.strip(),
                             "País": "Global",
                             "Posición": i+1,
                             "Plataforma": "BB Excl US"})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

@st.cache_data(ttl=300)
def fetch_circle():
    try:
        soup = BeautifulSoup(requests.get("https://circlechart.kr/page_chart/onoff.circle?nationGbn=T&serviceGbn=ALL", headers=HEADERS).text, "lxml")
        data = []
        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")
            if len(cols)>=5 and "babymonster" in cols[3].text.lower():
                data.append({"Canción": cols[2].text.strip(),
                             "País": "Korea",
                             "Posición": int(cols[0].text.strip()),
                             "Plataforma": "Circle"})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Canción","País","Posición","Plataforma"])

@st.cache_data(ttl=300)
def fetch_youtube():
    try:
        soup = BeautifulSoup(requests.get("https://kworb.net/youtube/trending.html", headers=HEADERS).text, "lxml")
        data = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols)>=5:
                title = cols[2].text.strip()
                if "babymonster" in title.lower():
                    views = int(cols[3].text.strip().replace(",",""))
                    data.append({"Canción": title,"Views": views})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Canción","Views"])

# ---------------- LOAD ----------------
df_all = pd.concat([
    fetch_itunes(),
    fetch_spotify(),
    fetch_billboard_global(),
    fetch_billboard_excl(),
    fetch_circle()
], ignore_index=True)

df_yt = fetch_youtube()

df_all["Posición"] = pd.to_numeric(df_all["Posición"], errors="coerce")

songs = df_all["Canción"].dropna().unique().tolist()
selected_song = st.selectbox("🎵 Selecciona canción", songs)

filtered = df_all[df_all["Canción"] == selected_song]

yt_filtered = df_yt[df_yt["Canción"].astype(str).str.contains(
    selected_song, case=False, na=False, regex=False
)] if not df_yt.empty else pd.DataFrame()

# ---------------- SCORE ----------------
def score_calc(df, yt):
    base = (100 - df["Posición"].fillna(100)).sum()
    yt_score = yt["Views"].sum()/1_000_000 if not yt.empty else 0
    return base + yt_score

score = score_calc(filtered, yt_filtered)

# ---------------- METRICS ----------------
st.subheader(selected_song)

c1,c2,c3,c4 = st.columns(4)

best = int(filtered["Posición"].min()) if not filtered.empty else 0
top10 = int((filtered["Posición"]<=10).sum()) if not filtered.empty else 0
avg = round(filtered["Posición"].mean(),1) if not filtered.empty else 0

c1.metric("🏆 Mejor", best)
c2.metric("🔥 Top 10", top10)
c3.metric("📊 Promedio", avg)
c4.metric("🌐 Score", int(score))

# ---------------- TABS ----------------
tab1,tab2,tab3 = st.tabs(["📊 Charts","🎥 YouTube","🏆 Ranking"])

with tab1:
    st.dataframe(filtered, use_container_width=True)

    fig = px.bar(filtered, x="Plataforma", y="Posición",
                 color="Plataforma", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if yt_filtered.empty:
        st.info("No hay trending ahora mismo")
    else:
        st.dataframe(yt_filtered)
        st.metric("Views", int(yt_filtered["Views"].sum()))

with tab3:
    ranking=[]
    for s in songs:
        f=df_all[df_all["Canción"]==s]
        yt=df_yt[df_yt["Canción"].astype(str).str.contains(s, case=False, regex=False)]
        ranking.append({"Canción":s,"Score":score_calc(f,yt)})
    ranking_df=pd.DataFrame(ranking).sort_values("Score",ascending=False)

    st.dataframe(ranking_df)

    fig=px.bar(ranking_df.head(10), x="Canción", y="Score",
               template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
if auto:
    time.sleep(60)
    st.rerun()
