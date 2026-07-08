import streamlit as st
import pandas as pd
import datetime
import json
from sqlalchemy import text
from google import genai
from google.genai import types

st.set_page_config(page_title="Jordi's Voedings & Trainings Tracker", layout="centered", page_icon="🏋️‍♂️")

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subheader { font-size: 16px; color: #4B5563; margin-bottom: 20px; }
    .meal-card { background-color: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #10B981; display: flex; justify-content: space-between; align-items: center; }
    .meal-type { font-weight: bold; color: #2563EB; font-size: 14px; }
    .macro-text { font-size: 12px; color: #6B7280; }
    .protein-success { background-color: #D1FAE5; color: #065F46; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-top: 10px; }
    .protein-warning { background-color: #FEE2E2; color: #991B1B; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-top: 10px; }
    .weight-card { background-color: #EFF6FF; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏋️‍♂️ Jordi\'s AI Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Beheer je doordeweekse tekort, trainingen, gewichtsverloop en automatische eiwitkoppeling.</div>', unsafe_allow_html=True)

# MET-waarden voor trainingen
met_values = {
    "Rustdag / Geen": 0, 
    "Push (Borst, Schouders, Triceps)": 5.0, 
    "Pull (Rug, Biceps)": 5.0, 
    "Legs (Benen, Buik)": 6.5, 
    "Keeperstraining (Matig intensief)": 5.0,
    "Voetbaltraining (Kelderklasse / Rustig)": 4.5
}

# --- PERMANENTE DATABASE FUNCTIES ---
conn = st.connection("local_db", type="sql")

with conn.session as session:
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS tracker_data (
            key TEXT PRIMARY KEY,
            json_payload TEXT
        )
    """))
    session.commit()

def load_all_data():
    try:
        df = conn.query(text("SELECT * FROM tracker_data"), ttl=0)
        db_dict = {}
        for index, row in df.iterrows():
            db_dict[row['key']] = json.loads(row['json_payload'])
        return db_dict
    except:
        return {}

def save_week_data(key, data):
    json_string = json.dumps(data)
    with conn.session as session:
        session.execute(
            text("INSERT OR REPLACE INTO tracker_data (key, json_payload) VALUES (:key, :json)"),
            {"key": key, "json": json_string}
        )
        session.commit()

if 'history_db' not in st.session_state:
    st.session_state['history_db'] = load_all_data()

# --- AI INTEGRATIE (GOOGLE GEMINI) ---
def extraheer_macros_met_ai(user_input):
    """Gestructureerde AI call naar Gemini om direct valide macro JSON terug te krijgen"""
    try:
        # Haal de API key op uit Streamlit Secrets
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        client = genai.Client(api_key=api_key)
        
        # We dwingen Gemini om exact ons JSON format te volgen via Structured Outputs
        class MaaltijdMacroDoel(types.BaseModel):
            kcal: int
            eiwit: int
            kh: int
            vet: int

        prompt = f"""
        Analyseer de volgende maaltijd en schat zo nauwkeurig mogelijk de macro's (Calorieën, Eiwit in grammen, Koolhydraten in grammen, Vet in grammen).
        Ga uit van standaard Nederlandse porties en voedingswaarden als er geen hoeveelheid bij staat.
        
        Maaltijd: "{user_input}"
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MaaltijdMacroDoel,
                temperature=0.1
            ),
        )
        
        # Zet het resultaat om naar een Python dict
        return json.loads(response.text)
    except Exception as e:
        st.error(f"AI Foutje: {e}")
        return None

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
    # HIER IS HET VERANDERD: 'huidige_week' in plaats van 'historische_week'
    if geselecteerd_jaar == huidig_jaar and w == huidige_week:
        weken_lijst.append(f"Week {w} (Huidige week)")
    else:
        weken_lijst.append(f"Week {w}")

geselecteerde_week_naam = st.sidebar.selectbox("Bekijk of bewerk week:", weken_lijst, index=0)
db_key = f"{geselecteerd_jaar}_{geselecteerde_week_naam}"

if db_key not in st.session_state['history_db']:
    st.session_state['history_db'][db_key] = {
        "gewicht": 85.0,
        "trainingen": {dag: "Rustdag / Geen" for dag in dagen_van_de_week},
        "duur": {dag: 0 for dag in dagen_van_de_week},
        "maaltijden_lijst": {dag: [] for dag in dagen_van_de_week},
        "wrap_check": {dag: False for dag in dagen_van_de_week}
    }

week_data = st.session_state['history_db'][db_key]

if "gewicht" not in week_data: week_data["gewicht"] = 85.0
if "maaltijden_lijst" not in week_data: week_data["maaltijden_lijst"] = {dag: [] for dag in dagen_van_de_week}
if "wrap_check" not in week_data: week_data["wrap_check"] = {dag: False for dag in dagen_van_de_week}

gewicht = week_data["gewicht"]
doel_eiwit = int(gewicht * 2)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Wekelijks Dashboard", "💪 Log Trainingen", "🍏 Log Voeding"])

with tab2:
    st.subheader(f"💪 Trainingen loggen voor {geselecteerde_week_naam}")
    extra_verbrand_totaal = 0
    for dag in dagen_van_de_week:
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            default_idx = list(met_values.keys()).index(week_data["trainingen"][dag])
            nieuwe_training = st.selectbox(f"Training op {dag}:", list(met_values.keys()), index=default_idx, key=f"t_{db_key}_{dag}")
            if nieuwe_training != week_data["trainingen"][dag]:
                week_data["trainingen"][dag] = nieuwe_training
                save_week_data(db_key, week_data)
                
        with col_d2:
            default_duur = int(week_data["duur"][dag])
            nieuwe_duur = st.number_input(f"Duur (min):", value=default_duur, step=5, key=f"d_{db_key}_{dag}")
            if nieuwe_duur != week_data["duur"][dag]:
                week_data["duur"][dag] = nieuwe_duur
                save_week_data(db_key, week_data)
        
        if week_data["trainingen"][dag] != "Rustdag / Geen":
            met = met_values[week_data["trainingen"][dag]]
            dag_verbranding = round((met * 3.5 * gewicht / 200) * week_data["duur"][dag])
            extra_verbrand_totaal += dag_verbranding

with tab3:
    st.subheader(f"🍏 Voeding & Eiwit Tracker")
    
    gekozen_dag = st.selectbox("Kies de dag:", dagen_van_de_week, key="food_day_selector")
    st.info(f"Je bewerkt nu: **{gekozen_dag}** van **{geselecteerde_week_naam}**")
    
    oude_wrap = week_data["wrap_check"][gekozen_dag]
    week_data["wrap_check"][gekozen_dag] = st.checkbox("Ik had die dag mijn vaste Ei-Chorizo-Andalouse Wrap op (627 kcal | 40g Eiwit)", value=week_data["wrap_check"][gekozen_dag], key=f"wrap_{db_key}_{gekozen_dag}")
    if oude_wrap != week_data["wrap_check"][gekozen_dag]:
        save_week_data(db_key, week_data)
    
    st.write("---")
    st.markdown("### 🤖 Live AI Maaltijd Scanner")
    
    gekozen_type = st.selectbox(
        "Wat voor soort maaltijd is dit?",
        ["Ontbijt", "Lunch", "Avondeten", "Snack"],
        key=f"type_sel_{db_key}_{gekozen_dag}"
    )
    
    ai_input = st.text_input("Wat heb je gegeten? (Echte AI berekent alles):", 
                            placeholder="Bijv: '200g biefstuk met 150g zilvervliesrijst en een lepel olijfolie'",
                            key=f"ai_in_{db_key}_{gekozen_dag}")
    
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        voeg_toe = st.button("✨ Bereken & Voeg toe")
        
    if voeg_toe and ai_input:
        with st.spinner("AI is ingrediënten aan het wegen... 🧠"):
            resultaat = extraheer_macros_met_ai(ai_input)
        
        if resultaat:
            nieuwe_maaltijd = {
                "Type": gekozen_type,
                "Omschrijving": ai_input,
                "Kcal": int(resultaat["kcal"]),
                "Eiwit": int(resultaat["eiwit"]),
                "Kh": int(resultaat["kh"]),
                "Vet": int(resultaat["vet"])
            }
            week_data["maaltijden_lijst"][gekozen_dag].append(nieuwe_maaltijd)
            save_week_data(db_key, week_data)
            st.success(f"Toegevoegd via Gemini AI! +{resultaat['eiwit']}g Eiwit")
            st.rerun()
        else:
            st.warning("Kon geen verbinding maken met de AI. Controleer of je de GEMINI_API_KEY correct hebt toegevoegd aan je Secrets.")

    # --- MAALTIJDEN OVERZICHT PER DAG ---
    st.write("### 📋 Log van vandaag")
    huidige_maaltijden = week_data["maaltijden_lijst"][gekozen_dag]
    
    tabel_kcal, tabel_eiwit, tabel_kh, tabel_vet = 0, 0, 0, 0
    for index, m in enumerate(huidige_maaltijden):
        m_kcal = m.get("Kcal", 0)
        m_eiwit = m.get("Eiwit", 0)
        m_kh = m.get("Kh", 0)
        m_vet = m.get("Vet", 0)
        
        tabel_kcal += m_kcal
        tabel_eiwit += m_eiwit
        tabel_kh += m_kh
        tabel_vet += m_vet
        
        col_m1, col_m2 = st.columns([5, 1])
        with col_m1:
            st.markdown(f"""
            <div class="meal-card">
                <div>
                    <span class="meal-type">[{m.get('Type', 'Snack')}]</span> {m.get('Omschrijving', '')}
                    <br><span class="macro-text">🧬 Eiwit: {m_eiwit}g | 🍞 KH: {m_kh}g | 🥑 Vet: {m_vet}g</span>
                </div>
                <div style="font-weight: bold; color: #4B5563;">{m_kcal} kcal</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            if st.button("🗑️", key=f"del_{db_key}_{gekozen_dag}_{index}"):
                week_data["maaltijden_lijst"][gekozen_dag].pop(index)
                save_week_data(db_key, week_data)
                st.rerun()

    wrap_kcal = 627 if week_data["wrap_check"][gekozen_dag] else 0
    wrap_eiwit = 40 if week_data["wrap_check"][gekozen_dag] else 0
    wrap_kh = 55 if week_data["wrap_check"][gekozen_dag] else 0
    wrap_vet = 25 if week_data["wrap_check"][gekozen_dag] else 0
    
    totaal_dag_kcal = int(tabel_kcal + wrap_kcal)
    totaal_dag_eiwit = int(tabel_eiwit + wrap_eiwit)
    totaal_dag_kh = int(tabel_kh + wrap_kh)
    totaal_dag_vet = int(tabel_vet + wrap_vet)
    
    st.write("### 📊 Totaal berekende macro's vandaag:")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Calorieën", f"{totaal_dag_kcal} kcal")
    c2.metric("🧬 Eiwitten", f"{totaal_dag_eiwit}g / {doel_eiwit}g")
    c3.metric("🍞 Koolhydraten", f"{totaal_dag_kh}g")
    c4.metric("🥑 Vetten", f"{totaal_dag_vet}g")

    if totaal_dag_eiwit >= doel_eiwit:
        st.markdown(f'<div class="protein-success">🎉 Eiwitdoel behaald! Je zit op {totaal_dag_eiwit}g.</div>', unsafe_allow_html=True)
    else:
        tekort = doel_eiwit - totaal_dag_eiwit
        st.markdown(f'<div class="protein-warning">⚠️ Je hebt nog {tekort}g eiwit nodig om je doel van {doel_eiwit}g te halen vandaag.</div>', unsafe_allow_html=True)

with tab1:
    st.subheader(f"De Wekelijkse Balans ({geselecteerde_week_naam})")
    
    st.markdown(f"""
    <div class="weight-card">
        ⚖️ <b>Gewichts- & Progressie Tracker</b><br>
        Vul hier je weegmoment in voor <b>{geselecteerde_week_naam}</b>. Je gekoppelde eiwitdoel voor deze week stelt zich automatisch in op 2g per kg (<b>{doel_eiwit}g</b>).
    </div>
    """, unsafe_allow_html=True)
    
    ouder_gewicht = week_data["gewicht"]
    week_data["gewicht"] = st.number_input(
        "Mijn gewicht deze week (kg):", min_value=50.0, max_value=150.0, value=float(week_data["gewicht"]), step=0.1, key=f"weight_input_{db_key}"
    )
    if ouder_gewicht != week_data["gewicht"]:
        save_week_data(db_key, week_data)
        st.rerun()
        
    st.write("---")
    
    doordeweeks_buffer = (doel_tekort * 6) + extra_verbrand_totaal
    netto_week_tekort = doordeweeks_buffer - cheat_overschot
    geschat_vetverlies = netto_week_tekort / 7000
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Totale Buffer (incl. sport)", f"-{doordeweeks_buffer} kcal")
    with col2: st.metric("Weekend Overschot", f"+{cheat_overschot} kcal")
    with col3: st.metric("Netto Weekresultaat", f"-{netto_week_tekort} kcal", delta=f"{geschat_vetverlies:.2f} kg vet/week")

    st.markdown("### 🗓️ Weekoverzicht, Gewicht & Eiwit Status")
    
    kcal_doel_lijst, kcal_werkelijk_lijst, status_lijst = [], [], []
    eiwit_lijst = []
    
    for dag in dagen_van_de_week:
        m_lijst = week_data["maaltijden_lijst"].get(dag, [])
        tabel_kcal_dag = sum([m.get("Kcal", 0) for m in m_lijst])
        tabel_eiwit_dag = sum([m.get("Eiwit", 0) for m in m_lijst])
        
        w_check = week_data["wrap_check"].get(dag, False)
        wrap_kcal_dag = 627 if w_check else 0
        wrap_eiwit_dag = 40 if w_check else 0
        
        kcal_werkelijk_lijst.append(int(tabel_kcal_dag + wrap_kcal_dag))
        
        totaal_eiwit_dag = int(tabel_eiwit_dag + wrap_eiwit_dag)
        if totaal_eiwit_dag >= doel_eiwit:
            eiwit_lijst.append(f"🟢 {totaal_eiwit_dag}g (Behaald)")
        else:
            eiwit_lijst.append(f"🔴 {totaal_eiwit_dag}g / {doel_eiwit}g")
        
        if dag == cheat_dag:
            kcal_doel_lijst.append(totaal_cheat_kcal)
            status_lijst.append("🍺 Cheatday")
        else:
            kcal_doel_lijst.append(doel_kcal)
            status_lijst.append("⚡ Strak Tekort")
            
    df_week = pd.DataFrame({
        "Dag": dagen_van_de_week,
        "Doel (kcal)": kcal_doel_lijst,
        "Inname (kcal)": kcal_werkelijk_lijst,
        "🧬 Eiwit Tracker": eiwit_lijst,
        "Status": status_lijst
    })
    st.dataframe(df_week, use_container_width=True)
    st.caption(f"Huidig geregistreerd gewicht voor deze week: **{week_data['gewicht']} kg**.")
