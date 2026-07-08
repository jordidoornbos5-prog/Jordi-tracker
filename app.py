import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Jordi's Voedings & Trainings Tracker", layout="centered", page_icon="🏋️‍♂️")

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subheader { font-size: 16px; color: #4B5563; margin-bottom: 20px; }
    .card { background-color: #F3F4F6; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #2563EB; }
    .metric-val { font-size: 22px; font-weight: bold; color: #111827; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏋️‍♂️ Jordi\'s AI Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Beheer je doordeweekse tekort, trainingen en je weekend budget in één oogopslag.</div>', unsafe_allow_html=True)

# MET-waarden voor trainingen (aangepast aan werkelijke intensiteit)
met_values = {
    "Rustdag / Geen": 0, 
    "Push (Borst, Schouders, Triceps)": 5.0, 
    "Pull (Rug, Biceps)": 5.0, 
    "Legs (Benen, Buik)": 6.5, 
    "Keeperstraining (Matig intensief)": 5.0,
    "Voetbaltraining (Kelderklasse / Rustig)": 4.5
}
gewicht = 85 # Gemiddeld gewicht voor de formule

# --- SIDEBAR: INSTELLINGEN ---
st.sidebar.header("🎯 Jouw Basis Profiel")
onderhoud_kcal = st.sidebar.number_input("Onderhoudsbehoefte (kcal/dag)", value=2500, step=50)
doel_tekort = st.sidebar.slider("Doordeweeks Doel Tekort (kcal)", 500, 1000, 800)
doel_kcal = onderhoud_kcal - doel_tekort

st.sidebar.header("🍺 Weekend Cheat Day")
dagen_van_de_week = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
cheat_dag = st.sidebar.selectbox("Kies jouw Cheatday:", dagen_van_de_week, index=6)

bier_flesjes = st.sidebar.number_input("Aantal flesjes Heineken op cheatday", value=15, step=1)
pizza_kcal = st.sidebar.number_input("Calorieën Pizza / Cheatmeal", value=950, step=50)

# Berekening cheatday calorieën
overdag_kcal = 1000 
totaal_bier_kcal = bier_flesjes * 125
totaal_cheat_kcal = totaal_bier_kcal + pizza_kcal + overdag_kcal
cheat_overschot = totaal_cheat_kcal - onderhoud_kcal

# --- DYNAMISCHE JAAR & WEKEN SELECTIE (ALLEEN VERLEDEN) ---
st.sidebar.header("📅 Selecteer Periode")

vandaag = datetime.date.today()
huidig_jaar = vandaag.year
huidige_week = vandaag.isocalendar()[1]

# Jaar selecteren (keuze uit huidige jaar en vorig jaar)
geselecteerd_jaar = st.sidebar.selectbox("Kies Jaar:", [huidig_jaar, huidig_jaar - 1], index=0)

# Bepaal tot welke week we mogen kijken
if geselecteerd_jaar == huidig_jaar:
    max_week = huidige_week
else:
    max_week = 52 # Als het een vorig jaar is, mag je alle 52 weken zien

# Bouw de lijst met weken omgekeerd op (nieuwste bovenaan)
weken_lijst = []
for w in range(max_week, 0, -1):
    if geselecteerd_jaar == huidig_jaar and w == huidige_week:
        weken_lijst.append(f"Week {w} (Huidige week)")
    else:
        weken_lijst.append(f"Week {w}")

geselecteerde_week_naam = st.sidebar.selectbox("Bekijk of bewerk week:", weken_lijst, index=0)

# Maak een unieke sleutel voor de database combinatie (bijv: "2026_Week 28")
db_key = f"{geselecteerd_jaar}_{geselecteerde_week_naam}"

# --- IN-MEMORY DATABASE SYSTEMEN ---
if 'history_db' not in st.session_state:
    st.session_state['history_db'] = {}

if db_key not in st.session_state['history_db']:
    st.session_state['history_db'][db_key] = {
        "trainingen": {dag: "Rustdag / Geen" for dag in dagen_van_de_week},
        "duur": {dag: 0 for dag in dagen_van_de_week},
        "voeding": {dag: "" for dag in dagen_van_de_week},
        "wrap_check": {dag: False for dag in dagen_van_de_week},
        "kcal_inname": {dag: 0 for dag in dagen_van_de_week}
    }

week_data = st.session_state['history_db'][db_key]

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "💪 Log Trainingen", "🍏 Log Voeding"])

with tab2:
    st.subheader(f"💪 Trainingen loggen voor {geselecteerde_week_naam} ({
