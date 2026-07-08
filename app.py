
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Jordi's Voedings & Trainings Tracker", layout="centered", page_icon="🏋️‍♂️")

# Custom Styling for Dark Theme
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subheader { font-size: 16px; color: #4B5563; margin-bottom: 20px; }
    .card { background-color: #F3F4F6; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #2563EB; }
    .metric-val { font-size: 22px; font-weight: bold; color: #111827; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏋️‍♂️ Jordi's AI Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Beheer je doordeweekse tekort, trainingen en je weekend budget in één oogopslag.</div>', unsafe_allow_html=True)

# Sidebar settings for configuration
st.sidebar.header("🎯 Jouw Basis Profiel")
onderhoud_kcal = st.sidebar.number_input("Onderhoudsbehoefte (kcal/dag)", value=2500, step=50)
doel_tekort = st.sidebar.slider("Doordeweeks Doel Tekort (kcal)", 500, 1000, 800)
doel_kcal = onderhoud_kcal - doel_tekort

st.sidebar.header("🍺 Weekend Cheat Day Instellingen")
bier_flesjes = st.sidebar.number_input("Aantal flesjes Heineken", value=15, step=1)
pizza_kcal = st.sidebar.number_input("Calorieën Pizza", value=950, step=50)

# Calculations for the weekly dashboard
overdag_kcal = 1000 # Normaal overdag eiwitrijk eten op cheatday
totaal_bier_kcal = bier_flesjes * 125
totaal_cheat_kcal = totaal_bier_kcal + pizza_kcal + overdag_kcal
cheat_overschot = totaal_cheat_kcal - onderhoud_kcal

# Tabs for layout
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "🍏 Log Voeding", "💪 Log Training"])

with tab1:
    st.subheader("De Wekelijkse Balans")
    
    # Simple simulated data state for 6 days
    doordeweeks_buffer = doel_tekort * 6
    netto_week_tekort = doordeweeks_buffer - cheat_overschot
    geschat_vetverlies = netto_week_tekort / 7000
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Doordeweekse Buffer", f"-{doordeweeks_buffer} kcal")
    with col2:
        st.metric("Weekend Overschot", f"+{cheat_overschot} kcal")
    with col3:
        st.metric("Netto Weekresultaat", f"-{netto_week_tekort} kcal", delta=f"{geschat_vetverlies:.2f} kg vet/week")

    st.markdown("### 🗓️ Weekoverzicht Planning")
    dagen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag (Cheatday)"]
    kcal_lijst = [doel_kcal]*6 + [totaal_cheat_kcal]
    status_lijst = ["⚡ Strak Tekort"]*6 + ["🍺 Cheatday"]
    
    df_week = pd.DataFrame({
        "Dag": dagen,
        "Geplande Inname (kcal)": kcal_lijst,
        "Status": status_lijst
    })
    st.dataframe(df_week, use_container_width=True)

with tab2:
    st.subheader("🍏 Wat heb je vandaag gegeten?")
    food_input = st.text_area("Typ hier in normaal Nederlands wat je op hebt (bijv: 'Mijn ontbijt wrap en 's avonds bami met extra kip'):")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        wrap_check = st.checkbox("Ik heb vandaag mijn vaste Ei-Chorizo-Andalouse Wrap op (627 kcal)")
    
    if st.button("Reken maaltijden uit via AI"):
        st.success("AI analyseert je input... (Dit koppel je morgen aan de echte Gemini API!)")
        totaal_vandaag = 627 if wrap_check else 0
        st.info(f"Huidige geregistreerde inname gebaseerd op selecties: **{totaal_vandaag} kcal**")

with tab3:
    st.subheader("💪 Training & Energieverbruik")
    training_type = st.selectbox("Welke training heb je gedaan?", ["Geen / Rustdag", "Push (Borst, Schouders, Triceps)", "Pull (Rug, Biceps)", "Legs (Benen, Buik)", "Cardio / Keepers-specifiek"])
    duur = st.slider("Duur van de training (minuten)", 30, 120, 60, step=5)
    
    # Calculate calories burned
    met_values = {"Geen / Rustdag": 0, "Push (Borst, Schouders, Triceps)": 5.0, "Pull (Rug, Biceps)": 5.0, "Legs (Benen, Buik)": 6.5, "Cardio / Keepers-specifiek": 7.5}
    gewicht = 85 # standard estimate for dynamic formula
    verbranding = round((met_values[training_type] * 3.5 * gewicht / 200) * duur) if training_type != "Geen / Rustdag" else 0
    
    if training_type != "Geen / Rustdag":
        st.markdown(f'<div class="card">🔥 Lekker gewerkt! Met je <b>{training_type}</b> training van {duur} minuten heb je naar schatting <b>{verbranding} calorieën</b> extra verbrand. Je spiermassa is weer optimaal geprikkeld voor herstel!</div>', unsafe_allow_html=True)
    else:
        st.info("Rustdag. Perfect om je spieren te laten groeien en herstellen met de juiste eiwitten!")
app.py
app.py weergeven.