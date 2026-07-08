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

# --- WEKEN SELECTIE (HISTORIE) ---
st.sidebar.header("📅 Selecteer Week")
huidige_week = datetime.date.today().isocalendar()[1]
geselecteerde_week = st.sidebar.selectbox(
    "Bekijk of bewerk week:", 
    [f"Week {huidige_week} (Huidige week)", f"Week {huidige_week-1}", f"Week {huidige_week-2}", f"Week {huidige_week-3}"],
    index=0
)

# --- IN-MEMORY DATABASE SYSTEMEN ---
if 'history_db' not in st.session_state:
    st.session_state['history_db'] = {}

if geselecteerde_week not in st.session_state['history_db']:
    st.session_state['history_db'][geselecteerde_week] = {
        "trainingen": {dag: "Rustdag / Geen" for dag in dagen_van_de_week},
        "duur": {dag: 0 for dag in dagen_van_de_week},
        "voeding": {dag: "" for dag in dagen_van_de_week},
        "wrap_check": {dag: False for dag in dagen_van_de_week},
        "kcal_inname": {dag: 0 for dag in dagen_van_de_week}
    }

week_data = st.session_state['history_db'][geselecteerde_week]

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "💪 Log Trainingen", "🍏 Log Voeding"])

with tab2:
    st.subheader(f"💪 Trainingen loggen voor {geselecteerde_week}")
    st.write("Pas hier de trainingen aan voor de geselecteerde week.")
    
    extra_verbrand_totaal = 0
    
    for dag in dagen_van_de_week:
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            default_idx = list(met_values.keys()).index(week_data["trainingen"][dag])
            week_data["trainingen"][dag] = st.selectbox(f"Training op {dag}:", list(met_values.keys()), index=default_idx, key=f"t_{geselecteerde_week}_{dag}")
        with col_d2:
            default_duur = int(week_data["duur"][dag])
            week_data["duur"][dag] = st.number_input(f"Duur (min):", value=default_duur, step=5, key=f"d_{geselecteerde_week}_{dag}")
        
        # Bereken verbranding per dag
        if week_data["trainingen"][dag] != "Rustdag / Geen":
            met = met_values[week_data["trainingen"][dag]]
            dag_verbranding = round((met * 3.5 * gewicht / 200) * week_data["duur"][dag])
            extra_verbrand_totaal += dag_verbranding

with tab3:
    st.subheader(f"🍏 Voeding loggen voor {geselecteerde_week}")
    
    gekozen_dag = st.selectbox("Kies de dag waarvoor je eten wilt invullen of terugkijken:", dagen_van_de_week)
    st.info(f"Je bewerkt nu: **{gekozen_dag}** van **{geselecteerde_week}**")
    
    # Haal opgeslagen data op of vul in
    week_data["voeding"][gekozen_dag] = st.text_area("Typ hier in normaal Nederlands wat je die dag op hebt:", value=week_data["voeding"][gekozen_dag], key=f"food_{geselecteerde_week}_{gekozen_dag}")
    week_data["wrap_check"][gekozen_dag] = st.checkbox("Ik had die dag mijn vaste Ei-Chorizo-Andalouse Wrap op (627 kcal)", value=week_data["wrap_check"][gekozen_dag], key=f"wrap_{geselecteerde_week}_{gekozen_dag}")
    
    st.write("---")
    base_kcal = 627 if week_data["wrap_check"][gekozen_dag] else 0
    
    if week_data["voeding"][gekozen_dag] != "" and week_data["kcal_inname"][gekozen_dag] == 0:
        week_data["kcal_inname"][gekozen_dag] = base_kcal + 1100 
    elif week_data["voeding"][gekozen_dag] == "" and not week_data["wrap_check"][gekozen_dag]:
        week_data["kcal_inname"][gekozen_dag] = 0
    elif week_data["voeding"][gekozen_dag] == "" and week_data["wrap_check"][gekozen_dag]:
        week_data["kcal_inname"][gekozen_dag] = 627
        
    week_data["kcal_inname"][geselecteerde_week + gekozen_dag] = st.number_input("Totaal berekende kcal voor deze dag:", value=int(week_data["kcal_inname"][gekozen_dag]), key=f"kcal_val_{geselecteerde_week}_{gekozen_dag}")

with tab1:
    st.subheader(f"De Wekelijkse Balans ({geselecteerde_week})")
    
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

    st.markdown("### 🗓️ Weekoverzicht & Werkelijke Inname")
    
    kcal_doel_lijst = []
    kcal_werkelijk_lijst = []
    status_lijst = []
    t_lijst = []
    
    for dag in dagen_van_de_week:
        t_lijst.append(week_data["trainingen"][dag])
        kcal_werkelijk_lijst.append(week_data["kcal_inname"][dag])
        if dag == cheat_dag:
            kcal_doel_lijst.append(totaal_cheat_kcal)
            status_lijst.append("🍺 Cheatday")
        else:
            kcal_doel_lijst.append(doel_kcal)
            status_lijst.append("⚡ Strak Tekort")
            
    df_week = pd.DataFrame({
        "Dag": dagen_van_de_week,
        "Doel Inname (kcal)": kcal_doel_lijst,
        "Werkelijke Inname (kcal)": kcal_werkelijk_lijst,
        "Gekozen Training": t_lijst,
        "Status": status_lijst
    })
    st.dataframe(df_week, use_container_width=True)
    
    totaal_doel_week = sum(kcal_doel_lijst)
    totaal_werkelijk_week = sum(kcal_werkelijk_lijst)
    st.info(f"📊 **Doel inname deze week:** {totaal_doel_week} kcal | **Jouw ingevoerde inname:** {totaal_werkelijk_week} kcal")
