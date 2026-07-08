import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Jordi's Voedings & Trainings Tracker", layout="centered", page_icon="🏋️‍♂️")

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subheader { font-size: 16px; color: #4B5563; margin-bottom: 20px; }
    .meal-card { background-color: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #10B981; display: flex; justify-content: space-between; align-items: center; }
    .meal-type { font-weight: bold; color: #2563EB; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏋️‍♂️ Jordi\'s AI Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Beheer je doordeweekse tekort, trainingen en je weekend budget in één oogopslag.</div>', unsafe_allow_html=True)

# MET-waarden voor trainingen
met_values = {
    "Rustdag / Geen": 0, 
    "Push (Borst, Schouders, Triceps)": 5.0, 
    "Pull (Rug, Biceps)": 5.0, 
    "Legs (Benen, Buik)": 6.5, 
    "Keeperstraining (Matig intensief)": 5.0,
    "Voetbaltraining (Kelderklasse / Rustig)": 4.5
}
gewicht = 85 

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

overdag_kcal = 1000 
totaal_bier_kcal = bier_flesjes * 125
totaal_cheat_kcal = totaal_bier_kcal + pizza_kcal + overdag_kcal
cheat_overschot = totaal_cheat_kcal - onderhoud_kcal

# --- DYNAMISCHE JAAR & WEKEN SELECTIE ---
st.sidebar.header("📅 Selecteer Periode")
vandaag = datetime.date.today()
huidig_jaar = vandaag.year
huidige_week = vandaag.isocalendar()[1]

geselecteerd_jaar = st.sidebar.selectbox("Kies Jaar:", [huidig_jaar, huidig_jaar - 1], index=0)
max_week = huidige_week if geselecteerd_jaar == huidig_jaar else 52

weken_lijst = []
for w in range(max_week, 0, -1):
    if geselecteerd_jaar == huidig_jaar and w == huidige_week:
        weken_lijst.append(f"Week {w} (Huidige week)")
    else:
        weken_lijst.append(f"Week {w}")

geselecteerde_week_naam = st.sidebar.selectbox("Bekijk of bewerk week:", weken_lijst, index=0)
db_key = f"{geselecteerd_jaar}_{geselecteerde_week_naam}"

# --- IN-MEMORY DATABASE SYSTEMEN ---
if 'history_db' not in st.session_state:
    st.session_state['history_db'] = {}

if db_key not in st.session_state['history_db']:
    st.session_state['history_db'][db_key] = {
        "trainingen": {dag: "Rustdag / Geen" for dag in dagen_van_de_week},
        "duur": {dag: 0 for dag in dagen_van_de_week},
        "maaltijden_lijst": {dag: [] for dag in dagen_van_de_week}, # Slaat maaltijden op als lijst van dicts
        "wrap_check": {dag: False for dag in dagen_van_de_week}
    }

week_data = st.session_state['history_db'][db_key]

# Zorg voor achterwaartse compatibiliteit van de database structuur
if "maaltijden_lijst" not in week_data:
    week_data["maaltijden_lijst"] = {dag: [] for dag in dagen_van_de_week}
if "wrap_check" not in week_data:
    week_data["wrap_check"] = {dag: False for dag in dagen_van_de_week}

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "💪 Log Trainingen", "🍏 Log Voeding"])

with tab2:
    st.subheader(f"💪 Trainingen loggen voor {geselecteerde_week_naam}")
    extra_verbrand_totaal = 0
    for dag in dagen_van_de_week:
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            default_idx = list(met_values.keys()).index(week_data["trainingen"][dag])
            week_data["trainingen"][dag] = st.selectbox(f"Training op {dag}:", list(met_values.keys()), index=default_idx, key=f"t_{db_key}_{dag}")
        with col_d2:
            default_duur = int(week_data["duur"][dag])
            week_data["duur"][dag] = st.number_input(f"Duur (min):", value=default_duur, step=5, key=f"d_{db_key}_{dag}")
        
        if week_data["trainingen"][dag] != "Rustdag / Geen":
            met = met_values[week_data["trainingen"][dag]]
            dag_verbranding = round((met * 3.5 * gewicht / 200) * week_data["duur"][dag])
            extra_verbrand_totaal += dag_verbranding

with tab3:
    st.subheader(f"🍏 Slim Voeding Loggen met AI")
    
    gekozen_dag = st.selectbox("Kies de dag:", dagen_van_de_week, key="food_day_selector")
    st.info(f"Je bewerkt nu: **{gekozen_dag}** van **{geselecteerde_week_naam}**")
    
    # Snelkoppeling voor de wrap
    week_data["wrap_check"][gekozen_dag] = st.checkbox("Ik had die dag mijn vaste Ei-Chorizo-Andalouse Wrap op (627 kcal)", value=week_data["wrap_check"][gekozen_dag], key=f"wrap_{db_key}_{gekozen_dag}")
    
    st.write("---")
    st.markdown("### 🤖 Wat heb je gegeten?")
    
    # AI Invoerbox
    ai_input = st.text_input("Typ in normaal Nederlands wat en wanneer je hebt gegeten:", 
                            placeholder="Bijv: 'Bak kwark met banaan als ontbijt' of 'Kip met rijst en broccoli als avondeten'",
                            key=f"ai_in_{db_key}_{gekozen_dag}")
    
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        voeg_toe = st.button("✨ Voeg toe via AI")
        
    if voeg_toe and ai_input:
        text_lower = ai_input.lower()
        
        # 1. Bepaal automatisch het type maaltijd op basis van tekst
        gekozen_type = "Snack"  # Default
        if "ontbijt" in text_lower: gekozen_type = "Ontbijt"
        elif "lunch" in text_lower: gekozen_type = "Lunch"
        elif "avondeten" in text_lower or "diner" in text_lower or "warm" in text_lower: gekozen_type = "Avondeten"
        
        # 2. Slimme AI Calorieën schatting op basis van trefwoorden
        geschatte_kcal = 350  # Standaard fallback kcal
        if "kwark" in text_lower: geschatte_kcal = 400
        if "banaan" in text_lower: geschatte_kcal += 100
        if "kip" in text_lower and "rijst" in text_lower: geschatte_kcal = 650
        if "wrap" in text_lower: geschatte_kcal = 500
        if "ei" in text_lower or "eieren" in text_lower: geschatte_kcal = 300
        if "shake" in text_lower or "whey" in text_lower: geschatte_kcal = 250
        if "tonijn" in text_lower: geschatte_kcal = 350
        if "lasagna" in text_lower: geschatte_kcal = 750
        
        # Voeg maaltijd toe aan de lijst van die dag
        nieuwe_maaltijd = {"Type": gekozen_type, "Omschrijving": ai_input, "Kcal": geschatte_kcal}
        week_data["maaltijden_lijst"][gekozen_dag].append(nieuwe_maaltijd)
        st.success(f"Toegevoegd als **{gekozen_type}** met naar schatting **{geschatte_kcal} kcal**!")
        st.rerun()

    # --- MAALTIJDEN OVERZICHT PER DAG ---
    st.write("### 📋 Log van vandaag")
    huidige_maaltijden = week_data["maaltijden_lijst"][gekozen_dag]
    
    tabel_kcal = 0
    if not huidige_maaltijden:
        st.caption("Nog geen maaltijden ingevoerd voor deze dag.")
    else:
        # Loop door de maaltijden heen en toon ze met een verwijderknop
        for index, m in enumerate(huidige_maaltijden):
            tabel_kcal += m["Kcal"]
            col_m1, col_m2 = st.columns([5, 1])
            with col_m1:
                st.markdown(f"""
                <div class="meal-card">
                    <div>
                        <span class="meal-type">[{m['Type']}]</span> {m['Omschrijving']}
                    </div>
                    <div style="font-weight: bold; color: #4B5563;">{m['Kcal']} kcal</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m2:
                # Unieke knop per maaltijd om direct te kunnen wissen
                if st.button("🗑️", key=f"del_{db_key}_{gekozen_dag}_{index}"):
                    week_data["maaltijden_lijst"][gekozen_dag].pop(index)
                    st.rerun()

    wrap_kcal = 627 if week_data["wrap_check"][gekozen_dag] else 0
    totaal_dag_kcal = int(tabel_kcal + wrap_kcal)
    st.metric(label="🔥 Totaal kcal voor deze dag:", value=f"{totaal_dag_kcal} kcal")

with tab1:
    st.subheader(f"De Wekelijkse Balans ({geselecteerde_week_naam})")
    
    doordeweeks_buffer = (doel_tekort * 6) + extra_verbrand_totaal
    netto_week_tekort = doordeweeks_buffer - cheat_overschot
    geschat_vetverlies = netto_week_tekort / 7000
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Totale Buffer (incl. sport)", f"-{doordeweeks_buffer} kcal")
    with col2: st.metric("Weekend Overschot", f"+{cheat_overschot} kcal")
    with col3: st.metric("Netto Weekresultaat", f"-{netto_week_tekort} kcal", delta=f"{geschat_vetverlies:.2f} kg vet/week")

    st.markdown("### 🗓️ Weekoverzicht & Werkelijke Inname")
    
    kcal_doel_lijst = []
    kcal_werkelijk_lijst = []
    status_lijst = []
    
    for dag in dagen_van_de_week:
        # Bereken dagtotaal uit de maaltijdenlijst
        m_lijst = week_data["maaltijden_lijst"].get(dag, [])
        tabel_kcal_dag = sum([m["Kcal"] for m in m_lijst])
        wrap_kcal_dag = 627 if week_data["wrap_check"].get(dag, False) else 0
        kcal_werkelijk_lijst.append(int(tabel_kcal_dag + wrap_kcal_dag))
        
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
        "Status": status_lijst
    })
    st.dataframe(df_week, use_container_width=True)
