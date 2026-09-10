import streamlit as st
import sqlite3
import uuid
import streamlit_authenticator as stauth
import bcrypt

# --- PAGE CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="Brawl Fantasy - Tournaments", page_icon="🎮", layout="centered")

# Minimal and clean CSS style
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0e1626 50%, #070a10 100%);
        background-attachment: fixed;
    }
    .stApp, .stApp *:not(.stTextInput input, button) {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #090d16 0%, #0e1626 50%, #070a10 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 2px solid rgba(255, 75, 75, 0.5) !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 500;
    }
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: white !important;
        background-color: rgba(255, 255, 255, 0.05);
        width: 100%;
    }
    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- USER DATABASE MANAGEMENT (SIGN UP & LOGIN) ---
def init_auth_db():
    conn = sqlite3.connect("brawl_fantasy.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utenti_registrati (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM utenti_registrati")
    if cursor.fetchone()[0] == 0:
        hashed_default = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT OR IGNORE INTO utenti_registrati VALUES (?, ?, ?, ?)", 
                       ('admin', 'Administrator', 'admin@brawlfantasy.com', hashed_default))
    conn.commit()
    conn.close()

init_auth_db()

def carica_credenziali():
    conn = sqlite3.connect("brawl_fantasy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, name, email, password FROM utenti_registrati")
    rows = cursor.fetchall()
    conn.close()
    
    usernames = {}
    for row in rows:
        usernames[row[0]] = {
            'name': row[1],
            'email': row[2],
            'password': row[3]
        }
    return {'usernames': usernames}

credentials = carica_credenziali()

authenticator = stauth.Authenticate(
    credentials,
    cookie_name='brawl_fantasy_cookie',
    cookie_key='chiave_segreta_molto_sicura',
    cookie_expiry_days=30
)

# --- LOGIN / SIGN UP SCREEN ---
if not st.session_state.get('authentication_status'):
    st.title("🎮 Brawl Fantasy - Access")
    
    scelta_auth = st.radio("Choose an option:", ["Login", "Register a new account"], horizontal=True)
    
    if scelta_auth == "Login":
        authenticator.login(location='main')
        if st.session_state.get('authentication_status') == False:
            st.error('Incorrect username or password.')
        elif st.session_state.get('authentication_status') == None:
            st.warning('Please enter your credentials or sign up if you do not have an account.')
            
    else:
        st.subheader("📝 New User Registration")
        with st.form("form_registrazione"):
            nuovo_user = st.text_input("Choose a Username")
            nuovo_nome = st.text_input("Full Name or Nickname")
            nuova_email = st.text_input("Email Address")
            nuova_pwd = st.text_input("Choose a Password", type="password")
            conferma_pwd = st.text_input("Confirm Password", type="password")
            
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                if not nuovo_user or not nuovo_nome or not nueva_email if 'nueva_email' in locals() else not nuova_email or not nuova_pwd:
                    st.error("All fields are required!")
                elif nuova_pwd != conferma_pwd:
                    st.error("Passwords do not match!")
                else:
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM utenti_registrati WHERE username = ?", (nuovo_user,))
                    if cursor.fetchone():
                        st.error("This username is already taken. Please choose another one.")
                        conn.close()
                    else:
                        hashed_pwd = bcrypt.hashpw(nuova_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute("INSERT INTO utenti_registrati (username, name, email, password) VALUES (?, ?, ?, ?)",
                                       (nuovo_user, nuovo_nome, nuova_email, hashed_pwd))
                        conn.commit()
                        conn.close()
                        st.success("Registration completed successfully! You can now go to 'Login' and sign in.")

# --- MAIN APPLICATION (AFTER LOGIN) ---
if st.session_state.get('authentication_status') == True:
    name = st.session_state.get('name')
    
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.markdown(f"Welcome, **{name}**!")
    st.sidebar.markdown("---")

    # --- MAIN DATABASE SETUP ---
    def init_db():
        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tornei (
                nome_torneo TEXT PRIMARY KEY,
                num_giornate INTEGER DEFAULT 4
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regolamenti (
                torneo TEXT PRIMARY KEY,
                testo_regolamento TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_giornate (
                torneo TEXT,
                giornata TEXT,
                num_team_scelti INTEGER DEFAULT 5,
                budget INTEGER DEFAULT 100,
                bloccato INTEGER DEFAULT 0,
                PRIMARY KEY (torneo, giornata)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_torneo (
                torneo TEXT,
                team TEXT,
                prezzo INTEGER,
                PRIMARY KEY (torneo, team)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_disponibili_giornata (
                torneo TEXT,
                giornata TEXT,
                team TEXT,
                PRIMARY KEY (torneo, giornata, team)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti_device (
                device_id TEXT PRIMARY KEY,
                utente TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rose (
                device_id TEXT,
                torneo TEXT,
                giornata TEXT,
                utente TEXT,
                formazione TEXT,
                spesa INTEGER,
                PRIMARY KEY (device_id, torneo, giornata)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS punteggi_ufficiali (
                torneo TEXT,
                giornata TEXT,
                team TEXT,
                punti INTEGER,
                PRIMARY KEY (torneo, giornata, team)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_risultati (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                torneo TEXT,
                giornata TEXT,
                data TEXT,
                orario TEXT,
                team_1 TEXT,
                team_2 TEXT,
                score_1 INTEGER,
                score_2 INTEGER,
                dettaglio_set TEXT
            )
        """)

        colonne_da_aggiungere = [
            ("config_giornate", "budget", "INTEGER DEFAULT 100"),
            ("config_giornate", "bloccato", "INTEGER DEFAULT 0"),
            ("match_risultati", "team_1", "TEXT"),
            ("match_risultati", "team_2", "TEXT"),
            ("match_risultati", "score_1", "INTEGER"),
            ("match_risultati", "score_2", "INTEGER"),
            ("match_risultati", "dettaglio_set", "TEXT")
        ]
        
        for tabella, colonna, tipo in colonne_da_aggiungere:
            try:
                cursor.execute(f"ALTER TABLE {tabella} ADD COLUMN {colonna} {tipo}")
            except sqlite3.OperationalError:
                pass
        
        cursor.execute("SELECT COUNT(*) FROM tornei")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO tornei (nome_torneo, num_giornate) VALUES (?, ?)", ("Last Chance Qualifier", 4))
            
            regolamento_default = (
                "### 📜 Welcome to Brawl Fantasy Rules!\n\n"
                "1. **Budget**: You have a specific budget in credits to spend on your lineup for each matchday.\n"
                "2. **Lineup**: Select the exact number of required teams for the matchday.\n"
                "3. **Scoring**: Points are updated officially after matches conclude.\n"
                "4. **Fair Play**: Have fun and enjoy the competition!"
            )
            cursor.execute("INSERT INTO regolamenti (torneo, testo_regolamento) VALUES (?, ?)", ("Last Chance Qualifier", regolamento_default))

            team_default = [
                ("Last Chance Qualifier", "Team Heretics", 32),
                ("Last Chance Qualifier", "Natus Vincere", 30),
                ("Last Chance Qualifier", "Loud", 28),
                ("Last Chance Qualifier", "Skcalalas EA", 24),
                ("Last Chance Qualifier", "Fut Freezone", 20),
                ("Last Chance Qualifier", "Kds Esports", 16),
                ("Last Chance Qualifier", "Trick Of China", 13),
                ("Last Chance Qualifier", "Ace Xero", 10)
            ]
            cursor.executemany("INSERT OR IGNORE INTO team_torneo (torneo, team, prezzo) VALUES (?, ?, ?)", team_default)
            
            lista_default_nomi = [t[1] for t in team_default]
            for i in range(1, 5):
                g_nome = f"Matchday {i}"
                cursor.execute(
                    "INSERT OR IGNORE INTO config_giornate (torneo, giornata, num_team_scelti, budget, bloccato) VALUES (?, ?, ?, ?, ?)",
                    ("Last Chance Qualifier", g_nome, 5, 100, 0)
                )
                for t_nome in lista_default_nomi:
                    cursor.execute(
                        "INSERT OR IGNORE INTO team_disponibili_giornata (torneo, giornata, team) VALUES (?, ?, ?)",
                        ("Last Chance Qualifier", g_nome, t_nome)
                    )
        
        conn.commit()
        conn.close()

    init_db()

    if 'device_id' not in st.session_state:
        st.session_state['device_id'] = str(uuid.uuid4())

    # --- COMMON HEADER ---
    st.title("🎮 Brawl Fantasy")
    st.subheader("🔥 Tournament & Competition Management")

    st.info("💡 **Note for participants:** For a better visual experience, it is recommended to set the application to **Dark Mode** using Streamlit settings.")

    st.markdown("---")

    conn = sqlite3.connect("brawl_fantasy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome_torneo, num_giornate FROM tornei")
    tornei_info = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    if not tornei_info:
        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tornei (nome_torneo, num_giornate) VALUES (?, ?)", ("Last Chance Qualifier", 4))
        cursor.execute("INSERT OR IGNORE INTO config_giornate (torneo, giornata, num_team_scelti, budget, bloccato) VALUES (?, ?, ?, ?, ?)", ("Last Chance Qualifier", "Matchday 1", 5, 100, 0))
        cursor.execute("INSERT OR IGNORE INTO regolamenti (torneo, testo_regolamento) VALUES (?, ?)", ("Last Chance Qualifier", "Default rules."))
        conn.commit()
        conn.close()
        tornei_info = {"Last Chance Qualifier": 4}

    st.sidebar.header("🏆 Active Tournament")
    lista_tornei = list(tornei_info.keys())

    torneo_selezionato = st.sidebar.radio(
        "Select Competition", 
        lista_tornei, 
        index=0 if lista_tornei else 0
    )

    tot_giornate = tornei_info.get(torneo_selezionato, 4)
    lista_giornate = [f"Matchday {i}" for i in range(1, tot_giornate + 1)]

    st.sidebar.header("📋 Main Menu")
    modalita = st.sidebar.radio(
        "Choose section:", 
        ["Rules & Regulations", "Homepage", "General Leaderboard", "Match Results", "Admin Area (Tournaments & Scores)"]
    )

    st.sidebar.header("📅 Matchday Selection")
    giornata_selezionata = st.sidebar.radio(
        "Select Matchday", 
        lista_giornate, 
        index=0 if lista_giornate else 0
    )

    conn = sqlite3.connect("brawl_fantasy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT num_team_scelti, budget, bloccato FROM config_giornate WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
    res_config = cursor.fetchone()
    conn.close()

    team_richiesti = res_config[0] if res_config else 5
    budget_giornata = res_config[1] if res_config and res_config[1] is not None else 100
    matchday_bloccato = res_config[2] if res_config and len(res_config) > 2 and res_config[2] is not None else 0

    st.sidebar.markdown("---")
    stato_badge = "🔴 Locked" if matchday_bloccato == 1 else "🟢 Open"
    st.sidebar.caption(
        f"**Tournament:** {torneo_selezionato}  \n"
        f"**Matchday:** {giornata_selezionata}  \n"
        f"**Required Teams:** {team_richiesti} | **Budget:** {budget_giornata}  \n"
        f"**Status:** {stato_badge}"
    )

    conn = sqlite3.connect("brawl_fantasy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT team, prezzo FROM team_torneo WHERE torneo = ?", (torneo_selezionato,))
    prezzi_team = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT team FROM team_disponibili_giornata WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
    team_disponibili_giornata_list = [row[0] for row in cursor.fetchall()]
    conn.close()


    # ==========================================
    # 0. RULES & REGULATIONS SECTION
    # ==========================================
    if modalita == "Rules & Regulations":
        st.subheader(f"📖 Rules & Regulations — {torneo_selezionato}")
        st.markdown("Read the official rules, guidelines, and scoring system for this competition.")

        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        cursor.execute("SELECT testo_regolamento FROM regolamenti WHERE torneo = ?", (torneo_selezionato,))
        res_reg = cursor.fetchone()
        conn.close()

        testo_regolamento_corrente = res_reg[0] if res_reg else ""

        if testo_regolamento_corrente:
            st.markdown(testo_regolamento_corrente)
        else:
            st.info("ℹ️ No official rules have been posted yet for this tournament.")

        st.divider()

        with st.expander("🔐 Edit Rules (Admin Only)"):
            password_rules = st.text_input("Admin Password", type="password", key="pwd_rules")
            if password_rules == "brawl2026":
                st.success("🔓 Admin authorized:")
                
                with st.form("form_modifica_regolamento"):
                    nuovo_testo = st.text_area(
                        "Edit Tournament Rules (Markdown supported):", 
                        value=testo_regolamento_corrente,
                        height=250
                    )
                    salva_regole_btn = st.form_submit_button("💾 Save Rules")
                    
                    if salva_regole_btn:
                        conn = sqlite3.connect("brawl_fantasy.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO regolamenti (torneo, testo_regolamento) 
                            VALUES (?, ?)
                        """, (torneo_selezionato, nuovo_testo))
                        conn.commit()
                        conn.close()
                        st.success("✅ Rules updated successfully!")
                        st.rerun()
            else:
                if password_rules != "":
                    st.error("❌ Incorrect password.")


    # ==========================================
    # 1. HOMEPAGE (LINEUP BUILDER)
    # ==========================================
    elif modalita == "Homepage":
        st.markdown(f"### 🛒 Lineup Builder — {torneo_selezionato}")
        st.markdown(f"Manage your roster for **{giornata_selezionata}** (Required teams: **{team_richiesti}** | Budget: **{budget_giornata}**)")

        if matchday_bloccato == 1:
            st.warning(f"🔒 **Submissions for {giornata_selezionata} are currently locked by the administrator!**")
        else:
            st.caption("⏱️ **Notice:** You have time until one minute before the start of the competition to create or modify your lineup.")

        if not team_disponibili_giornata_list:
            st.warning(f"⚠️ There are no active teams configured as available for '{giornata_selezionata}' yet.")
        else:
            conn = sqlite3.connect("brawl_fantasy.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT utente FROM utenti_device WHERE device_id = ?", (st.session_state['device_id'],))
            res_device_user = cursor.fetchone()
            nome_fissato = res_device_user[0] if res_device_user else name

            cursor.execute("SELECT utente, formazione FROM rose WHERE device_id = ? AND torneo = ? AND giornata = ?", 
                           (st.session_state['device_id'], torneo_selezionato, giornata_selezionata))
            risultato_esistente = cursor.fetchone()
            conn.close()

            if not nome_fissato and risultato_esistente:
                nome_fissato = risultato_esistente[0]

            formazione_esistente = [t.strip() for t in risultato_esistente[1].split(",")] if risultato_esistente else []
            formazione_esistente = [t for t in formazione_esistente if t in team_disponibili_giornata_list]

            if nome_fissato:
                st.caption(f"👤 Linked device name: **{nome_fissato}**")

            disable_inputs = (matchday_bloccato == 1)

            st.markdown("#### 👤 Your Name / Team Nickname")
            nome_utente = st.text_input("Enter your unique nickname for this device:", value=nome_fissato, disabled=disable_inputs, label_visibility="collapsed")
            nome_pulito = nome_utente.strip()

            st.markdown("<br>", unsafe_allow_html=True)

            team_selezionati = st.multiselect(
                f"Select your {team_richiesti} teams (from available teams):",
                options=team_disponibili_giornata_list,
                default=formazione_esistente,
                disabled=disable_inputs
            )

            spesa_totale = sum(prezzi_team.get(t, 0) for t in team_selezionati)
            crediti_rimasti = budget_giornata - spesa_totale

            col1, col2 = st.columns(2)
            col1.metric("Selected Teams", f"{len(team_selezionati)} / {team_richiesti}")
            col2.metric("Remaining Credits", f"{crediti_rimasti} / {budget_giornata}", delta=-spesa_totale)

            formazione_valida = True
            if len(team_selezionati) != team_richiesti:
                st.warning(f"⚠️ You must select exactly {team_richiesti} teams.")
                formazione_valida = False
            elif spesa_totale > budget_giornata:
                st.error(f"❌ Budget exceeded! You have spent more than {budget_giornata} credits.")
                formazione_valida = False
            else:
                st.success("✅ **Valid Lineup!**")

            if matchday_bloccato == 0:
                if st.button("💾 Save / Update Lineup"):
                    if not nome_pulito:
                        st.error("❌ You must enter your Name or Nickname before saving!")
                    elif not formazione_valida:
                        st.error("❌ The lineup is not valid, cannot save.")
                    else:
                        formazione_str = ", ".join(team_selezionati)
                        conn = sqlite3.connect("brawl_fantasy.db")
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO utenti_device (device_id, utente) 
                            VALUES (?, ?)
                        """, (st.session_state['device_id'], nome_pulito))
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO rose (device_id, torneo, giornata, utente, formazione, spesa) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (st.session_state['device_id'], torneo_selezionato, giornata_selezionata, nome_pulito, formazione_str, spesa_totale))
                        
                        cursor.execute("""
                            UPDATE rose SET utente = ? WHERE device_id = ?
                        """, (nome_pulito, st.session_state['device_id']))

                        conn.commit()
                        conn.close()
                        st.success(f"🎉 Lineup successfully saved for **{nome_pulito}**!")
                        st.rerun()

        st.divider()
        st.subheader(f"👥 Registered Teams List — {torneo_selezionato} ({giornata_selezionata})")
        
        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        cursor.execute("SELECT utente, formazione, spesa FROM rose WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
        tutte_le_rose = cursor.fetchall()
        conn.close()

        if tutte_le_rose:
            for r in tutte_le_rose:
                st.markdown(
                    f"""
                    <div style="padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 8px; background-color: rgba(255,255,255,0.02);">
                        👤 <b>{r[0]}</b> — Lineup: <i>{r[1]}</i> <span style="color: #a0a0a0; float: right;">({r[2]} credits)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No lineups registered for this matchday in this tournament.")


    # ==========================================
    # 2. GENERAL LEADERBOARD & MATCHDAY STANDINGS
    # ==========================================
    elif modalita == "General Leaderboard":
        st.subheader(f"🏆 Leaderboards — {torneo_selezionato}")
        
        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT utente, giornata, formazione FROM rose WHERE torneo = ?", (torneo_selezionato,))
        tutte_le_rose_torneo = cursor.fetchall()
        
        cursor.execute("SELECT giornata, team, punti FROM punteggi_ufficiali WHERE torneo = ?", (torneo_selezionato,))
        punti_rows = cursor.fetchall()
        
        cursor.execute("SELECT utente, formazione FROM rose WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
        rose_giornata = cursor.fetchall()
        
        cursor.execute("SELECT team, punti FROM punteggi_ufficiali WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
        punti_giornata_rows = cursor.fetchall()
        conn.close()

        dizionario_punti_totale = {(row[0], row[1]): row[2] for row in punti_rows}
        dizionario_punti_singola = {row[0]: row[1] for row in punti_giornata_rows}

        st.markdown(f"### 🌐 General Cumulative Leaderboard (All Matchdays)")
        
        if tutte_le_rose_torneo:
            statistiche_utenti = {}

            for utente, giornata, formazione_str in tutte_le_rose_torneo:
                if utente not in statistiche_utenti:
                    statistiche_utenti[utente] = {"punti_totali": 0, "dettaglio_giornate": []}
                
                lista_team_utente = [t.strip() for t in formazione_str.split(",")]
                punti_giornata_utente = sum(dizionario_punti_totale.get((giornata, t), 0) for t in lista_team_utente)
                
                statistiche_utenti[utente]["punti_totali"] += punti_giornata_utente
                statistiche_utenti[utente]["dettaglio_giornate"].append({
                    "giornata": giornata,
                    "formazione": formazione_str,
                    "punti": punti_giornata_utente
                })

            classifica_generale = [
                {"utente": utente, **dati} for utente, dati in statistiche_utenti.items()
            ]
            classifica_generale = sorted(classifica_generale, key=lambda x: x["punti_totali"], reverse=True)

            for i, pos in enumerate(classifica_generale, 1):
                st.markdown(
                    f"""
                    <div style="padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px; background-color: rgba(255,255,255,0.02);">
                        <b>{i}° place: {pos['utente']}</b> — <span style="color: #4cd137; font-weight: bold;">{pos['punti_totali']} Total Points</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                with st.expander(f"📊 View breakdown for {pos['utente']}"):
                    for dg in pos["dettaglio_giornate"]:
                        st.write(f"- **{dg['giornata']}**: Lineup: *{dg['formazione']}* → **{dg['punti']} pts**")
        else:
            st.info("No lineups registered across any matchday for this tournament yet.")

        st.divider()

        st.markdown(f"### 📅 Matchday Standings — {giornata_selezionata}")

        if rose_giornata:
            classifica_giornata_lista = []
            for utente, formazione_str in rose_giornata:
                lista_team_utente = [t.strip() for t in formazione_str.split(",")]
                punti_totali_giornata = sum(dizionario_punti_singola.get(t, 0) for t in lista_team_utente)
                classifica_giornata_lista.append({
                    "utente": utente,
                    "formazione": formazione_str,
                    "punti": punti_totali_giornata
                })

            classifica_giornata_lista = sorted(classifica_giornata_lista, key=lambda x: x["punti"], reverse=True)

            for i, item in enumerate(classifica_giornata_lista, 1):
                st.markdown(
                    f"""
                    <div style="padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px; background-color: rgba(255,255,255,0.02);">
                        <b>{i}° place: {item['utente']}</b> — <span style="color: #4cd137; font-weight: bold;">{item['punti']} pts</span> <span style="color: #a0a0a0; font-size: 0.9em;">(Lineup: <i>{item['formazione']}</i>)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info(f"No lineups registered for **{giornata_selezionata}** yet.")


    # ==========================================
    # 3. MATCH RESULTS SECTION
    # ==========================================
    elif modalita == "Match Results":
        st.subheader(f"⚔️ Matches & Results — {torneo_selezionato} ({giornata_selezionata})")
        st.markdown("Match schedule, structured scores (Best of 5 sets), and official times.")

        conn = sqlite3.connect("brawl_fantasy.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, data, orario, team_1, team_2, score_1, score_2, dettaglio_set 
            FROM match_risultati WHERE torneo = ? AND giornata = ?
        """, (torneo_selezionato, giornata_selezionata))
        match_salvati = cursor.fetchall()
        conn.close()

        if match_salvati:
            for m in match_salvati:
                data_str = f"📅 {m[1]}" if m[1] else ""
                orario_str = f"⏰ {m[2]}" if m[2] else ""
                info_tempo = f" | {data_str} {orario_str}".strip() if (m[1] or m[2]) else ""
                
                t1, t2, s1, s2 = m[3], m[4], m[5], m[6]
                dettaglio = m[7] if m[7] else ""
                
                st.markdown(
                    f"""
                    <div style="padding: 14px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.12); margin-bottom: 12px; background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.15em; font-weight: bold; color: #ffffff;">{t1}</span> 
                                <span style="font-size: 0.9em; color: #a0a0a0; margin: 0 8px;">vs</span> 
                                <span style="font-size: 1.15em; font-weight: bold; color: #ffffff;">{t2}</span>
                            </div>
                            <div>
                                <span style="font-size: 1.3em; font-weight: bold; background-color: rgba(255,75,75,0.15); color: #ff4b4b; padding: 4px 12px; border-radius: 6px; border: 1px solid rgba(255,75,75,0.3);">{s1} - {s2}</span>
                            </div>
                        </div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(255,255,255,0.06);">
                        <small style="color: #a0a0a0;">Set details: {dettaglio} {info_tempo}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No matches or results entered for this matchday.")

        st.divider()

        with st.expander("🔐 Insert / Edit Match (Admin Structured Menu)"):
            password_match = st.text_input("Admin Password", type="password", key="pwd_match")
            if password_match == "brawl2026":
                st.success("🔓 Admin authorized:")
                
                lista_teams_disponibili_torneo = list(prezzi_team.keys())
                
                if len(lista_teams_disponibili_torneo) < 2:
                    st.warning("⚠️ You need at least 2 teams configured in this tournament to schedule a match.")
                else:
                    with st.form("form_inserisci_match_strutturato"):
                        col_d, col_o = st.columns(2)
                        with col_d:
                            data_match = st.text_input("Date (e.g. October 12)")
                        with col_o:
                            orario_match = st.text_input("Time (e.g. 15:30)")
                        
                        st.markdown("---")
                        
                        team_uno = st.selectbox("Team 1", lista_teams_disponibili_torneo, key="sel_t1")
                        default_t2_idx = 1 if len(lista_teams_disponibili_torneo) > 1 else 0
                        team_due = st.selectbox("Team 2", lista_teams_disponibili_torneo, index=default_t2_idx, key="sel_t2")
                        
                        st.markdown("#### 🔢 Score (Best of 5 Sets)")
                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            score_uno = st.number_input(f"Sets won by {team_uno}", min_value=0, max_value=5, value=3)
                        with col_s2:
                            score_due = st.number_input(f"Sets won by {team_due}", min_value=0, max_value=5, value=0)
                        
                        dettaglio_set_input = st.text_input("Set details / partials (e.g. Set 1: 3-1, Set 2: 3-0, Set 3: 3-2)")
                        
                        salva_match_btn = st.form_submit_button("➕ Save Structured Match Result")
                        
                        if salva_match_btn:
                            if team_uno == team_due:
                                st.error("❌ Team 1 and Team 2 cannot be the same team!")
                            else:
                                conn = sqlite3.connect("brawl_fantasy.db")
                                cursor = conn.cursor()
                                cursor.execute(
                                    """
                                    INSERT INTO match_risultati 
                                    (torneo, giornata, data, orario, team_1, team_2, score_1, score_2, dettaglio_set) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        torneo_selezionato, 
                                        giornata_selezionata, 
                                        data_match.strip(), 
                                        orario_match.strip(), 
                                        team_uno, 
                                        team_due, 
                                        score_uno, 
                                        score_due, 
                                        dettaglio_set_input.strip()
                                    )
                                )
                                conn.commit()
                                conn.close()
                                st.success("✅ Match result added successfully!")
                                st.rerun()

                if match_salvati:
                    st.markdown("#### 🗑️ Remove an entered match:")
                    opzioni_match = {f"{m[3]} vs {m[4]} ({m[5]}-{m[6]})": m[0] for m in match_salvati}
                    match_da_rimuovere = st.selectbox("Select match to delete:", list(opzioni_match.keys()))
                    if st.button("🗑️ Delete Selected Match"):
                        id_elimina = opzioni_match[match_da_rimuovere]
                        conn = sqlite3.connect("brawl_fantasy.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM match_risultati WHERE id = ?", (id_elimina,))
                        conn.commit()
                        conn.close()
                        st.success("✅ Match deleted successfully!")
                        st.rerun()
            else:
                if password_match != "":
                    st.error("❌ Incorrect password.")


    # ==========================================
    # 4. ADMIN AREA
    # ==========================================
    elif modalita == "Admin Area (Tournaments & Scores)":
        st.subheader("⚙️ Advanced Administrator Panel")
        password = st.text_input("Enter Admin Password", type="password")

        if password == "brawl2026":
            st.success("🔓 Admin access authorized!")
            
            st.markdown("### 🏟️ Tournaments & Matchdays Management")
            with st.form("form_nuovo_torneo"):
                col_tn, col_ng = st.columns([2, 1])
                with col_tn:
                    nuovo_torneo_input = st.text_input("Tournament Name (new or existing to update matchdays)")
                with col_ng:
                    giornate_torneo_input = st.number_input("Number of Matchdays", min_value=1, max_value=20, value=4)
                
                crea_torneo_btn = st.form_submit_button("💾 Save Tournament / Update Matchdays")
                if crea_torneo_btn and nuovo_torneo_input.strip():
                    t_nome = nuovo_torneo_input.strip()
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO tornei (nome_torneo, num_giornate) VALUES (?, ?)
                        ON CONFLICT(nome_torneo) DO UPDATE SET num_giornate = ?
                    """, (t_nome, giornate_torneo_input, giornate_torneo_input))
                    
                    cursor.execute("INSERT OR IGNORE INTO regolamenti (torneo, testo_regolamento) VALUES (?, ?)", (t_nome, "Default rules."))

                    cursor.execute("SELECT team FROM team_torneo WHERE torneo = ?", (t_nome,))
                    t_esistenti_torneo = [row[0] for row in cursor.fetchall()]

                    for i in range(1, giornate_torneo_input + 1):
                        g_nome = f"Matchday {i}"
                        cursor.execute("""
                            INSERT OR IGNORE INTO config_giornate (torneo, giornata, num_team_scelti, budget, bloccato) 
                            VALUES (?, ?, 5, 100, 0)
                        """, (t_nome, g_nome))
                        for t_item in t_esistenti_torneo:
                            cursor.execute("""
                                INSERT OR IGNORE INTO team_disponibili_giornata (torneo, giornata, team) 
                                VALUES (?, ?, ?)
                            """, (t_nome, g_nome, t_item))
                        
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Tournament '{t_nome}' configured with {giornate_torneo_input} matchdays!")
                    st.rerun()

            st.markdown(f"#### ⚙️ Configure Teams Count, Budget & Lock Status per Matchday ({torneo_selezionato})")
            with st.form("form_config_team_giornata"):
                giornata_da_configurare = st.selectbox("Select Matchday to configure:", lista_giornate, key="sel_cfg_count")
                
                conn = sqlite3.connect("brawl_fantasy.db")
                cursor = conn.cursor()
                cursor.execute("SELECT num_team_scelti, budget, bloccato FROM config_giornate WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_da_configurare))
                res_curr = cursor.fetchone()
                conn.close()
                val_attuale_config = res_curr[0] if res_curr and res_curr[0] is not None else 5
                budget_attuale_config = res_curr[1] if res_curr and res_curr[1] is not None else 100
                bloccato_attuale_config = bool(res_curr[2]) if res_curr and len(res_curr) > 2 and res_curr[2] is not None else False

                col_cf1, col_cf2 = st.columns(2)
                with col_cf1:
                    num_team_input = st.number_input("Required Teams count:", min_value=1, max_value=15, value=val_attuale_config)
                with col_cf2:
                    budget_input = st.number_input("Budget (Credits):", min_value=1, max_value=1000, value=budget_attuale_config)
                
                lock_input = st.checkbox("🔒 Lock Submissions (Prevent users from creating/editing lineups for this matchday)", value=bloccato_attuale_config)
                
                salva_config_btn = st.form_submit_button("💾 Save Matchday Configuration")
                if salva_config_btn:
                    val_bloccato_int = 1 if lock_input else 0
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO config_giornate (torneo, giornata, num_team_scelti, budget, bloccato) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (torneo_selezionato, giornata_da_configurare, num_team_input, budget_input, val_bloccato_int))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Matchday '{giornata_da_configurare}' for '{torneo_selezionato}' updated!")
                    st.rerun()

            st.markdown(f"#### 🏟️ Configure Available Teams per Matchday ({torneo_selezionato})")
            if prezzi_team:
                with st.form("form_config_team_disponibili"):
                    giornata_disp_config = st.selectbox("Select Matchday to configure available teams:", lista_giornate, key="sel_cfg_disp")
                    
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT team FROM team_disponibili_giornata WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_disp_config))
                    attualmente_abilitati = [row[0] for row in cursor.fetchall()]
                    conn.close()

                    if not attualmente_abilitati and prezzi_team:
                        attualmente_abilitati = list(prezzi_team.keys())

                    team_selezionati_admin = st.multiselect(
                        "Active Teams for this Matchday:",
                        options=list(prezzi_team.keys()),
                        default=attualmente_abilitati
                    )

                    salva_disp_btn = st.form_submit_button("💾 Save Available Teams for Matchday")
                    if salva_disp_btn:
                        conn = sqlite3.connect("brawl_fantasy.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM team_disponibili_giornata WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_disp_config))
                        for t_sel in team_selezionati_admin:
                            cursor.execute("INSERT INTO team_disponibili_giornata (torneo, giornata, team) VALUES (?, ?, ?)", (torneo_selezionato, giornata_disp_config, t_sel))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Available teams for '{giornata_disp_config}' updated successfully!")
                        st.rerun()
            else:
                st.info("⚠️ Add some teams to this tournament first before configuring matchday availability.")

            st.markdown("#### 🗑️ Delete an existing tournament:")
            torneo_da_eliminare = st.selectbox("Select tournament to delete:", list(tornei_info.keys()), key="select_delete_torneo")
            if st.button("❌ Delete Entire Tournament", type="primary"):
                if len(tornei_info) <= 1:
                    st.error("❌ You cannot delete the only tournament available!")
                else:
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tornei WHERE nome_torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM regolamenti WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM config_giornate WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM team_disponibili_giornata WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM team_torneo WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM rose WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM punteggi_ufficiali WHERE torneo = ?", (torneo_da_eliminare,))
                    cursor.execute("DELETE FROM match_risultati WHERE torneo = ?", (torneo_da_eliminare,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Tournament '{torneo_da_eliminare}' deleted successfully!")
                    st.rerun()

            st.divider()

            st.markdown(f"### 🏷️ Manage Teams and Prices for: **{torneo_selezionato}**")
            with st.form("form_aggiungi_team"):
                col_t, col_p = st.columns([2, 1])
                with col_t:
                    nome_nuovo_team = st.text_input("Team Name")
                with col_p:
                    prezzo_nuovo_team = st.number_input("Price (Credits)", min_value=1, max_value=100, value=20)
                
                aggiungi_team_btn = st.form_submit_button("➕ Save / Update Team Price")
                if aggiungi_team_btn and nome_nuovo_team.strip():
                    t_pulito = nome_nuovo_team.strip()
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO team_torneo (torneo, team, prezzo) VALUES (?, ?, ?)",
                                   (torneo_selezionato, t_pulito, prezzo_nuovo_team))
                    
                    for g_item in lista_giornate:
                        cursor.execute("""
                            INSERT OR IGNORE INTO team_disponibili_giornata (torneo, giornata, team) 
                            VALUES (?, ?, ?)
                        """, (torneo_selezionato, g_item, t_pulito))

                    conn.commit()
                    conn.close()
                    st.success(f"✅ Team '{t_pulito}' updated successfully!")
                    st.rerun()

            if prezzi_team:
                st.markdown("#### Teams currently registered in this tournament:")
                for t, p in prezzi_team.items():
                    st.write(f"- **{t}**: {p} credits")
                    
                st.markdown("#### 🗑️ Delete a team from this tournament:")
                team_da_eliminare = st.selectbox("Select team to remove:", list(prezzi_team.keys()), key="select_delete_team")
                if st.button("❌ Remove Team from Tournament", type="secondary"):
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM team_torneo WHERE torneo = ? AND team = ?", (torneo_selezionato, team_da_eliminare))
                    cursor.execute("DELETE FROM team_disponibili_giornata WHERE torneo = ? AND team = ?", (torneo_selezionato, team_da_eliminare))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Team '{team_da_eliminare}' removed successfully!")
                    st.rerun()

            st.divider()

            st.markdown(f"### 📝 Enter Official Points ({torneo_selezionato} - {giornata_selezionata})")
            if prezzi_team:
                conn = sqlite3.connect("brawl_fantasy.db")
                cursor = conn.cursor()
                cursor.execute("SELECT team, punti FROM punteggi_ufficiali WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
                punti_esistenti = {row[0]: row[1] for row in cursor.fetchall()}
                conn.close()

                with st.form("form_admin_punti"):
                    punti_inseriti = {}
                    for team in prezzi_team.keys():
                        valore_iniziale = punti_esistenti.get(team, 0)
                        punti_inseriti[team] = st.number_input(
                            f"Points for {team}", 
                            min_value=0, 
                            value=valore_iniziale, 
                            step=1, 
                            key=f"admin_{team}"
                        )
                    
                    salva_punti = st.form_submit_button("💾 Save Official Points")
                    if salva_punti:
                        conn = sqlite3.connect("brawl_fantasy.db")
                        cursor = conn.cursor()
                        for team, pt in punti_inseriti.items():
                            cursor.execute("INSERT OR REPLACE INTO punteggi_ufficiali (torneo, giornata, team, punti) VALUES (?, ?, ?, ?)",
                                           (torneo_selezionato, giornata_selezionata, team, pt))
                        conn.commit()
                        conn.close()
                        st.success("✅ Official points saved successfully!")
                        st.rerun()

            st.divider()

            st.markdown(f"### 🗑️ Manage Lineups ({torneo_selezionato} - {giornata_selezionata})")
            conn = sqlite3.connect("brawl_fantasy.db")
            cursor = conn.cursor()
            cursor.execute("SELECT device_id, utente, formazione FROM rose WHERE torneo = ? AND giornata = ?", (torneo_selezionato, giornata_selezionata))
            rose_per_elimina = cursor.fetchall()
            conn.close()

            if rose_per_elimina:
                opzioni_rose = {f"{r[1]} ({r[2]})": r[0] for r in rose_per_elimina}
                rosa_scelta_label = st.selectbox("Select lineup to delete:", list(opzioni_rose.keys()))

                if st.button("🗑️ Delete Selected Lineup", type="primary"):
                    id_da_eliminare = opzioni_rose[rosa_scelta_label]
                    conn = sqlite3.connect("brawl_fantasy.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM rose WHERE device_id = ? AND torneo = ? AND giornata = ?", (id_da_eliminare, torneo_selezionato, giornata_selezionata))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Lineup deleted successfully!")
                    st.rerun()
            else:
                st.info("No lineups registered for this matchday.")

        else:
            if password != "":
                st.error("❌ Incorrect password.")
            st.info("🔒 Enter the correct password to unlock the admin area.")
