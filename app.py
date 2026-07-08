import streamlit as st
import pandas as pd
import datetime
import json
import os
from sqlalchemy import text
from google import genai
from google.genai import types
from pydantic import BaseModel

st.set_page_config(page_title="Jordi's Performance Tracker", layout="wide", page_icon="🏋️‍♂️")

# --- CSS STYLING ---
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    .meal-card { background-color: #F9FAFB; padding: 10px; border-radius: 8px; border-left: 4px solid #10B981; margin-bottom: 5px; }
    .weight-card { background-color: #EFF6FF; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE ---
conn = st.connection("local_db", type="sql")
with conn.session as session:
    session.execute(text("CREATE TABLE IF NOT EXISTS tracker_data (key TEXT PRIMARY KEY, json_payload TEXT)"))
    session.commit()

if 'history_db' not in st.session_state:
    df = conn.query(text("SELECT * FROM tracker_data"), ttl=0)
    st.session_state['history_db'] = {row['key']: json.loads(row['json_payload']) for _, row in df.iterrows()}

def save_to_db(key, data):
    st.session_state['history_db'][key] = data
    with conn.session as session:
        session.execute(text("INSERT OR REPLACE INTO tracker_data (key, json_payload) VALUES (:key, :json)"),
                        {"key": key, "json": json.dumps(data)})
        session.commit()

# --- CONFIG & INITIALISATIE ---
dagen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
met_values = {"Rustdag / Geen": 0, "Push": 5.0, "Pull": 5.0, "Legs": 6.5, "Voetbal": 4.5}

st.sidebar.header("🎯 Instellingen")
onderhoud = st.sidebar.number_input("Onderhoud (kcal)", value=2500)
tekort = st.sidebar.slider("Doel Tekort", 500, 1000, 800)
cheat_dag = st.sidebar.selectbox("Cheatday", dagen, index=6)

geselecteerd_jaar = st.sidebar.selectbox("Jaar", [datetime.date.today().year, datetime.date.today().year-1])
week_naam = st.sidebar.selectbox("Week", [f"Week {w}" for w in range(52, 0, -1)])
db_key = f"{geselecteerd_jaar}_{week_naam}"

if db_key not in st.session_state['history_db']:
    st.session_state['history_db'][db_key] = {
        "gewicht": 85.0, "trainingen": {d: "Rustdag / Geen" for d in dagen},
        "duur": {d: 0 for d in dagen}, "maaltijden_lijst": {d: [] for d in dagen}, "wrap_check": {d: False for d in dagen}
    }
    save_to_db(db_key, st.session_state['history_db'][db_key])

wd = st.session_state['history_db'][db_key]

# --- AI ---
def ai_call(text_in):
    raw_key = st.secrets.get("GEMINI_API_KEY")
    if not raw_key: return None
    os.environ["GEMINI_API_KEY"] = str(raw_key).strip().replace('"', '').replace("'", "")
    try:
        class M(BaseModel): kcal: int; eiwit: int; kh: int; vet: int
        client = genai.Client()
        resp = client.models.generate_content(model='gemini-2.5-flash', contents=f"Analyseer: {text_in}",
               config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=M))
        return json.loads(resp.text)
    except: return None

# --- UI ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💪 Training", "🍏 Voeding"])

with tab1:
    st.markdown('<div class="main-header">Jordi\'s Performance Dashboard</div>', unsafe_allow_html=True)
    n_gewicht = st.number_input("Gewicht (kg)", value=float(wd["gewicht"]))
    if n_gewicht != wd["gewicht"]:
        wd["gewicht"] = n_gewicht
        save_to_db(db_key, wd)
    
    # Berekeningen
    tot_sport = sum([(met_values[wd["trainingen"][d]] * 3.5 * wd["gewicht"] / 200) * wd["duur"][d] for d in dagen])
    tekort_week = (tekort * 6) + tot_sport
    st.metric("Netto weekresultaat (kcal)", f"-{int(tekort_week)} kcal", delta=f"{-(tekort_week/7000):.2f} kg vet/week")

with tab2:
    for d in dagen:
        c1, c2 = st.columns(2)
        with c1:
            nt = st.selectbox(f"{d}:", list(met_values.keys()), index=list(met_values.keys()).index(wd["trainingen"].get(d, "Rustdag / Geen")), key=f"t_{d}")
            if nt != wd["trainingen"][d]: wd["trainingen"][d] = nt; save_to_db(db_key, wd)
        with c2:
            nd = st.number_input(f"Duur {d} (min)", value=wd["duur"].get(d, 0), key=f"dur_{d}")
            if nd != wd["duur"][d]: wd["duur"][d] = nd; save_to_db(db_key, wd)

with tab3:
    gd = st.selectbox("Dag", dagen)
    wrap = st.checkbox("Wrap (627kcal/40gE)", value=wd["wrap_check"].get(gd, False), key=f"wr_{gd}")
    if wrap != wd["wrap_check"].get(gd): wd["wrap_check"][gd] = wrap; save_to_db(db_key, wd)
    
    ai_in = st.text_input("Wat gegeten?")
    if st.button("✨ Bereken"):
        res = ai_call(ai_in)
        if res:
            wd["maaltijden_lijst"][gd].append({"Omschrijving": ai_in, **res})
            save_to_db(db_key, wd)
            st.rerun()
            
    for i, m in enumerate(wd["maaltijden_lijst"][gd]):
        st.markdown(f'<div class="meal-card">{m["Omschrijving"]} | {m["kcal"]}kcal | {m["eiwit"]}g Eiwit</div>', unsafe_allow_html=True)
        if st.button("Verwijder", key=f"del_{i}"): wd["maaltijden_lijst"][gd].pop(i); save_to_db(db_key, wd); st.rerun()
