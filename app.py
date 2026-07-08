import streamlit as st
import pandas as pd

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

# MET-waarden voor trainingen (verbranding berekening)
met_values = {
    "Rustdag / Geen": 0, 
    "Push (Borst, Schouders, Triceps)": 5.0, 
    "Pull (Rug, Biceps)": 5.0, 
    "Legs (Benen, Buik)": 6.5, 
    "Cardio / Keepers-specifiek": 7.5
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

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "💪 Log Trainingen", "🍏 Log Voeding"])

with tab2:
    st.subheader("💪 Wat voor trainingen doe je deze week?")
    st.write("Selecteer per dag wat je hebt gedaan en hoe lang. Dit verhoogt je wekelijkse calorieënbuffer!")
    
    trainingen_vandaag = {}
    duur_vandaag = {}
    extra_verbrand_totaal = 0
    
    # Maak handige kolommen voor de dagen van de week
    for dag in dagen_van_de_week:
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            trainingen_vandaag[dag] = st.selectbox(f"Training op {dag}:", list(met_values.keys()), key=f"t_{dag}")
        with col_d2:
            duur_vandaag[dag] = st.number_input(f"Duur (min):", value=60 if trainingen_vandaag[dag] != "Rustdag / Geen" else 0, step=5, key=f"d_{dag}")
        
        # Bereken verbranding per dag
        if trainingen_vandaag[dag] != "Rustdag / Geen":
            met = met_values[trainingen_vandaag[dag]]
            dag_verbranding = round((met * 3.5 * gewicht / 200) * duur_vandaag[dag])
            extra_verbrand_totaal += dag_verbranding

with tab1:
    st.subheader("De Wekelijkse Balans")
    
    # Berekeningen op basis van 6 dagen tekort + 1 cheatday
    doordeweeks_buffer = (doel_tekort * 6) + extra_verbrand_totaal
    netto_week_tekort = doordeweeks_buffer - cheat_overschot
    geschat_vetverlies = netto_week_tekort / 7000
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale Buffer (incl. sport)", f"-{doordeweeks_buffer} kcal")
    with col2:
        st.metric("Weekend Overschot", f"+{cheat_overschot} kcal")
    with col3:
        st.metric("Netto Weekresultaat", f"-{netto_week_tekort} kcal", delta=f"{geschat_vetverlies:.2f} kg vet/week")

    st.markdown("### 🗓️ Dynamisch Weekoverzicht")
    
    # Bouw het weekoverzicht dynamisch op op basis van de gekozen cheatday
    kcal_lijst = []
    status_lijst = []
    t_lijst = []
    
    for dag in dagen_van_de_week:
        t_lijst.append(trainingen_vandaag[dag])
        if dag == cheat_dag:
            kcal_lijst.append(totaal_cheat_kcal)
            status_lijst.append("🍺 Cheatday")
        else:
            kcal_lijst.append(doel_kcal)
            status_lijst.append("⚡ Strak Tekort")
            
    df_week = pd.DataFrame({
        "Dag": dagen_van_de_week,
        "Geplande Inname (kcal)": kcal_lijst,
        "Gekozen Training": t_lijst,
        "Status": status_lijst
    })
    st.dataframe(df_week, use_container_width=True)
    
    if extra_verbrand_totaal > 0:
        st.success(f"🔥 Door je trainingen heb je deze week naar schatting **{extra_verbrand_totaal} kcal** extra verbrand! Je wekelijkse marge is hiermee flink vergroot.")

with tab3:
    st.subheader("🍏 Log Voeding (AI)")
    food_input = st.text_area("Typ hier in normaal Nederlands wat je vandaag op hebt:")
    wrap_check = st.checkbox("Ik heb vandaag m've vaste Ei-Chorizo-Andalouse Wrap op (627 kcal)")
    
    if st.button("Reken maaltijd uit"):
        st.info("Sla dit op en we koppelen morgen de live AI-berekening!")
