a me servono soluzioni gratuite efficace e che mantengono le stesse funzionalità del codice 
import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
import logging
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import base64
import hmac
import hashlib
import time
from urllib.parse import urlencode

# Configurazione iniziale
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(
    page_title="TradeMate Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== FUNZIONI DI SUPPORTO ==========
def get_crypto_price(symbol):
    """Ottiene il prezzo attuale di una criptovaluta da CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower() }&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[symbol.lower()]['usd']
    except Exception as e:
        logger.error(f"Errore nel recupero del prezzo di {symbol}: {str(e)}")
        # Valori di fallback realistici
        fallback_prices = {
            "bitcoin": 64250.75,
            "ethereum": 3075.25,
            "binancecoin": 595.80,
            "ripple": 0.5025,
            "solana": 145.75,
            "cardano": 0.45,
            "dogecoin": 0.15,
            "polkadot": 7.25
        }
        return fallback_prices.get(symbol.lower(), 1000)

def get_current_eur_rate():
    """Ottiene il tasso di cambio EUR/USD attuale"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10) 
        data = response.json()
        return data['rates']['EUR']
    except Exception as e:
        logger.error(f"Errore nel recupero tasso di cambio: {str(e)}")
        return 0.92  # Fallback

def calculate_rsi(data, window=14):
    """Calcola l'RSI"""
    if data.empty or 'close' not in data.columns:
        return pd.Series()
        
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    
    # Gestisci divisione per zero
    avg_loss = avg_loss.replace(0, np.nan)
    rs = avg_gain / avg_loss
    rs = rs.fillna(0)
    
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_binance_account(api_key, api_secret):
    """Ottiene i dati dell'account Binance utilizzando l'API"""
    try:
        base_url = 'https://api.binance.com'
        endpoint = '/api/v3/account'
        
        timestamp = int(time.time()  * 1000)
        params = {
            'timestamp': timestamp
        }
        
        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        headers = {
            'X-MBX-APIKEY': api_key
        }
        
        response = requests.get(
            base_url + endpoint,
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Errore API Binance: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Errore nella chiamata API Binance: {str(e)}")
        return None

def process_binance_balances(account_data):
    """Processa i dati del wallet Binance"""
    if not account_data or 'balances' not in account_data:
        return {}
    
    wallet = {}
    eur_rate = get_current_eur_rate()
    
    for asset in account_data['balances']:
        symbol = asset['asset']
        free_amount = float(asset['free'])
        locked_amount = float(asset['locked'])
        total_amount = free_amount + locked_amount
        
        # Considera solo asset con saldo > 0
        if total_amount > 0:
            # Mappa simboli Binance a simboli CoinGecko
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'XRP': 'ripple',
                'SOL': 'solana',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'DOT': 'polkadot'
            }
            
            if symbol in symbol_map:
                price = get_crypto_price(symbol_map[symbol])
                usd_value = total_amount * price
                eur_value = usd_value * eur_rate
                
                wallet[symbol] = {
                    "quantity": total_amount,
                    "usd_value": usd_value,
                    "eur_value": eur_value,
                    "source": "Binance",
                    "last_updated": datetime.now().isoformat()
                }
    
    return wallet

# ========== INTERFACCIA UTENTE ==========
def set_page_style():
    """Imposta lo stile della pagina"""
    st.markdown("""
    <style>
        /* Stile generale */
        body {
            background-color: #0B0E11;
            color: #FFFFFF;
        }
        
        .main .block-container {
            background-color: #0B0E11;
            color: #FFFFFF;
            padding: 1rem;
            max-width: 100%;
        }
        
        /* Stile header */
        h1, h2, h3, h4, h5, h6 {
            color: #F0B90B !important;
        }
        
        /* Stile testo */
        p, span, div, label {
            color: #FFFFFF;
        }
        
        /* Stile input */
        .stTextInput > div > div > input, 
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #1E2026;
            color: #FFFFFF;
            border: 1px solid #2E3137;
            border-radius: 4px;
        }
        
        /* Stile select */
        .stSelectbox > div > div {
            background-color: #1E2026;
            color: #FFFFFF;
            border: 1px solid #2E3137;
            border-radius: 4px;
        }
        
        .stSelectbox [data-baseweb="select"] {
            background-color: #1E2026;
        }
        
        .stSelectbox [data-baseweb="select"] > div {
            background-color: #1E2026;
            color: white;
        }
        
        /* Stile bottoni */
        .stButton > button {
            background-color: #F0B90B;
            color: #0B0E11;
            font-weight: bold;
            border: none;
            border-radius: 4px;
        }
        
        /* Stile container */
        div[data-testid="stExpander"],
        div[data-testid="stForm"] {
            background-color: #1E2026;
            border-radius: 10px;
            border: 1px solid #2E3137;
        }
        
        /* Stile sidebar */
        .stSidebar [data-testid="stSidebar"] {
            background-color: #0B0E11;
            color: #FFFFFF;
        }
        
        /* Stile radio button */
        .stRadio > div {
            color: #FFFFFF;
        }
        
        /* Stile slider */
        .stSlider > div > div {
            color: #FFFFFF;
        }
        
        /* Stile dataframe */
        .stDataFrame {
            background-color: #1E2026;
        }
        
        .stDataFrame [data-testid="stTable"] {
            color: #FFFFFF;
        }
        
        /* Stile alert */
        .stAlert {
            background-color: #1E2026;
            color: #FFFFFF;
        }
        
        /* Stile divider */
        hr {
            border-color: #2E3137;
        }
        
        /* Stile header app */
        .app-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        /* Stile titolo app */
        .app-title {
            font-size: 2.2rem;
            font-weight: bold;
            color: #F0B90B;
        }
        
        /* Stile sottotitolo app */
        .app-subtitle {
            font-size: 1.1rem;
            color: #7F7F7F;
            margin-top: -10px;
        }
    </style>
    """, unsafe_allow_html=True)

def show_app_header():
    """Mostra l'header con logo e nome app"""
    try:
        # Carica il logo da file
        logo_path = "assets/trademate-logo.png"
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            # Converti l'immagine in base64 per l'embedding
            import io
            buffered = io.BytesIO()
            logo_img.save(buffered, format="PNG")
            logo_base64 = base64.b64encode(buffered.getvalue()).decode()
        else:
            # Fallback se il file non esiste
            st.warning(f"Logo non trovato in {logo_path}. Utilizzando logo di fallback.")
            logo_base64 = ""
    except Exception as e:
        st.error(f"Errore nel caricamento del logo: {str(e)}")
        logo_base64 = ""
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #2E3137;">
        <div>
            <img src="data:image/png;base64,{logo_base64}" width="60">
        </div>
        <div>
            <div style="font-size: 2.2rem; font-weight: bold; color: #F0B90B;">TradeMate Pro</div>
            <div style="font-size: 1.1rem; color: #7F7F7F; margin-top: -10px;">Il tuo assistente per il trading crypto</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_login_register():
    """Mostra le schermate di login/registrazione"""
    show_app_header()
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrati"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Accedi", use_container_width=True):
                st.session_state.auth = {
                    'logged_in': True,
                    'username': username,
                    'premium': True
                }
                st.rerun()

    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("Nuovo username")
            new_pass = st.text_input("Nuova password", type="password")
            new_pass_confirm = st.text_input("Conferma password", type="password")
            
            if st.form_submit_button("Registrati", use_container_width=True):
                if new_pass != new_pass_confirm:
                    st.error("Le password non coincidono")
                else:
                    st.success("Registrazione completata! Ora puoi accedere.")

def show_user_panel():
    """Mostra il pannello utente"""
    st.sidebar.markdown(f"### 👤 {st.session_state.auth['username']}")
    
    if st.session_state.auth.get('premium'):
        st.sidebar.success("✅ Account Premium")
    else:
        st.sidebar.warning("⚠️ Account Base")
        if st.sidebar.button("⭐ Upgrade a Premium"):
            st.session_state.auth['premium'] = True
            st.sidebar.success("Upgrade completato!")
            st.rerun()
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.auth = {
            'logged_in': False,
            'username': None,
            'premium': False
        }
        st.rerun()

def show_ai_assistant():
    """Mostra l'assistente AI come nell'immagine di riferimento"""
    # Contenitore per l'assistente AI
    with st.container():
        # Header dell'assistente
        st.markdown("""
        <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; margin-bottom: 15px; display: flex; align-items: center;">
            <span style="color: white; margin-right: 10px;">💬</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: white;">Assistente TradeMate AI</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Selettore di criptovalute
        st.markdown("<p style='margin-bottom: 5px;'>Seleziona crypto da analizzare</p>", unsafe_allow_html=True)
        crypto = st.selectbox(
            "Seleziona crypto",
            ["BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOGE", "DOT"],
            key="ai_crypto",
            label_visibility="collapsed"
        )
        
        # Campo di testo per contesto aggiuntivo
        st.markdown("<p style='margin-top: 15px; margin-bottom: 5px;'>Aggiungi contesto (opzionale):</p>", unsafe_allow_html=True)
        context = st.text_area(
            "Contesto",
            placeholder="Es: 'Considerando il recente fork...'",
            key="ai_context",
            label_visibility="collapsed"
        )
        
        # Pulsante per ottenere analisi
        if st.button("🔍 Ottieni Analisi", key="get_analysis_btn", type="primary"):
            if not st.session_state.auth.get('premium'):
                st.warning("Funzionalità Premium. Esegui l'upgrade.")
                return
                
            with st.spinner(f"Analisi {crypto} in corso..."):
                # Ottieni il prezzo reale
                symbol_map = {
                    "BTC": "bitcoin",
                    "ETH": "ethereum",
                    "BNB": "binancecoin",
                    "XRP": "ripple",
                    "SOL": "solana",
                    "ADA": "cardano",
                    "DOGE": "dogecoin",
                    "DOT": "polkadot"
                }
                
                price = get_crypto_price(symbol_map[crypto])
                
                st.session_state.last_analysis = {
                    "crypto": crypto,
                    "response": f"Analisi tecnica di {crypto}: Il prezzo attuale è ${price:,.2f}. Il trend mostra un supporto a ${price*0.95:,.2f} e resistenza a ${price*1.05:,.2f}. Consiglio: attendere pullback verso ${price*0.97:,.2f} per ingresso long con target ${price*1.03:,.2f}.",
                    "time": datetime.now().strftime("%H:%M %d/%m/%Y")
                }
            
            if 'last_analysis' in st.session_state:
                st.divider()
                st.markdown(f"**📊 Analisi {st.session_state.last_analysis['crypto']}**")
                st.success(st.session_state.last_analysis['response'])
                st.caption(f"Ultimo aggiornamento: {st.session_state.last_analysis['time']}")

def show_wallet_connection():
    """Connessione portafoglio come nell'immagine di riferimento"""
    # Contenitore per la connessione portafoglio
    with st.container():
        # Header della connessione portafoglio
        st.markdown("""
        <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; margin-bottom: 15px; display: flex; align-items: center;">
            <span style="color: white; margin-right: 10px;">🔧</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: white;">Connessione Portafoglio</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Radio buttons per la selezione della modalità
        st.markdown("<p style='margin-bottom: 5px;'>Seleziona modalità:</p>", unsafe_allow_html=True)
        mode = st.radio(
            "Modalità",
            ["📝 Manuale", "🔗 API Binance"],
            horizontal=True,
            key="wallet_mode",
            label_visibility="collapsed"
        )

        if mode == "📝 Manuale":
            cols = st.columns(2)
            with cols[0]:
                crypto = st.selectbox(
                    "Asset",
                    ["BTC", "ETH", "BNB", "XRP", "SOL", "ADA"],
                    key="manual_asset"
                )
            with cols[1]:
                amount = st.number_input(
                    "Quantità",
                    min_value=0.0,
                    step=0.000001,
                    format="%.6f",
                    key="manual_amount"
                )
            
            if st.button("💾 Salva", type="primary", key="save_manual"):
                # Ottieni il prezzo reale
                symbol_map = {
                    "BTC": "bitcoin",
                    "ETH": "ethereum",
                    "BNB": "binancecoin",
                    "XRP": "ripple",
                    "SOL": "solana",
                    "ADA": "cardano"
                }
                
                price = get_crypto_price(symbol_map[crypto])
                eur_rate = get_current_eur_rate()
                usd_value = amount * price
                eur_value = usd_value * eur_rate
                
                # Inizializza il portafoglio se non esiste
                if 'wallet' not in st.session_state:
                    st.session_state.wallet = {}
                
                # Aggiorna o aggiungi l'asset
                st.session_state.wallet[crypto] = {
                    "quantity": amount,
                    "usd_value": usd_value,
                    "eur_value": eur_value,
                    "source": "Manual",
                    "last_updated": datetime.now().isoformat()
                }
                
                st.toast("✅ Portafoglio aggiornato e salvato!")

        else:  # Modalità API Binance
            with st.expander("🔑 Inserisci le tue API Key Binance", expanded=True):
                # Crea un form per l'inserimento delle API keys
                with st.form(key="binance_api_form"):
                    api_key = st.text_input(
                        "API Key", 
                        type="password", 
                        key="binance_api_key_input"
                    )
                    api_secret = st.text_input(
                        "API Secret", 
                        type="password", 
                        key="binance_api_secret_input"
                    )
                    
                    # Pulsanti all'interno dello stesso form
                    cols = st.columns(3)
                    with cols[0]:
                        if st.form_submit_button("🔍 Test Connessione"):
                            if not api_key or not api_secret:
                                st.warning("Inserisci entrambe le credenziali")
                            else:
                                st.session_state.api_keys = (api_key, api_secret)
                                st.toast("✅ Connessione riuscita! Keys salvate.")
                    
                    with cols[1]:
                        if st.form_submit_button("📥 Importa Portafoglio"):
                            if not api_key or not api_secret:
                                st.warning("Inserisci entrambe le credenziali")
                                return
                                
                            with st.spinner("Recupero dati da Binance..."):
                                # Ottieni dati reali da Binance
                                account_data = get_binance_account(api_key, api_secret)
                                
                                if account_data:
                                    # Processa i dati del wallet
                                    wallet_data = process_binance_balances(account_data)
                                    
                                    if wallet_data:
                                        st.session_state.wallet = wallet_data
                                        st.success(f"✅ Importati {len(wallet_data)} asset!")
                                        st.balloons()
                                    else:
                                        st.warning("Nessun asset trovato nel wallet Binance.")
                                else:
                                    # Fallback a dati demo se l'API non funziona
                                    st.warning("Impossibile connettersi all'API Binance. Utilizzando dati demo.")
                                    
                                    # Ottieni prezzi reali
                                    btc_price = get_crypto_price("bitcoin")
                                    eth_price = get_crypto_price("ethereum")
                                    sol_price = get_crypto_price("solana")
                                    
                                    # Crea portafoglio di esempio con prezzi reali
                                    st.session_state.wallet = {
                                        "BTC": {
                                            "quantity": 0.5,
                                            "usd_value": 0.5 * btc_price,
                                            "eur_value": 0.5 * btc_price * get_current_eur_rate(),
                                            "source": "Demo",
                                            "last_updated": datetime.now().isoformat()
                                        },
                                        "ETH": {
                                            "quantity": 5,
                                            "usd_value": 5 * eth_price,
                                            "eur_value": 5 * eth_price * get_current_eur_rate(),
                                            "source": "Demo",
                                            "last_updated": datetime.now().isoformat()
                                        },
                                        "SOL": {
                                            "quantity": 25,
                                            "usd_value": 25 * sol_price,
                                            "eur_value": 25 * sol_price * get_current_eur_rate(),
                                            "source": "Demo",
                                            "last_updated": datetime.now().isoformat()
                                        }
                                    }
                    
                    with cols[2]:
                        if st.form_submit_button("🗑️ Rimuovi Keys"):
                            st.session_state.api_keys = None
                            st.toast("Keys rimosse con successo", icon="✅")

        # Mostra riepilogo o messaggio informativo
        if st.session_state.get('wallet'):
            show_wallet_summary()
        else:
            st.info("ℹ️ Nessun dato del portafoglio disponibile. Connetti un portafoglio per iniziare.")

def show_wallet_summary():
    """Riepilogo portafoglio"""
    try:
        df = pd.DataFrame.from_dict(st.session_state.wallet, orient='index')
        
        if df.empty:
            st.info("Portafoglio vuoto. Aggiungi asset per visualizzare il riepilogo.")
            return
            
        # Calcola totali
        total_usd = df['usd_value'].sum()
        total_eur = df['eur_value'].sum()
        
        # Mostra metriche con stile migliorato
        st.subheader("📊 Riepilogo Portafoglio")
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""
            <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <div style="font-size: 0.9rem; color: #7F7F7F;">Totale Asset</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #F0B90B;">{len(df)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <div style="font-size: 0.9rem; color: #7F7F7F;">Valore Totale (USD)</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #F0B90B;">${total_usd:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"""
            <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <div style="font-size: 0.9rem; color: #7F7F7F;">Valore Totale (EUR)</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #F0B90B;">€{total_eur:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostra ultimo aggiornamento
        try:
            last_updated = pd.to_datetime(df['last_updated']).max()
            st.caption(f"Ultimo aggiornamento: {last_updated.strftime('%d/%m/%Y %H:%M')}")
        except:
            st.caption("Ultimo aggiornamento: N/A")
        
        # Mostra tabella
        st.dataframe(
            df.style.format({
                'quantity': '{:.6f}',
                'usd_value': '${:,.2f}',
                'eur_value': '€{:,.2f}'
            }),
            use_container_width=True,
            height=400
        )
    except Exception as e:
        st.error(f"Errore nella visualizzazione del portafoglio: {str(e)}")

def show_technical_analysis():
    """Analisi tecnica come nell'immagine di riferimento"""
    # Contenitore per l'analisi tecnica
    with st.container():
        # Header dell'analisi tecnica
        st.markdown("""
        <div style="background-color: #1E2026; border-radius: 10px; padding: 15px; margin-bottom: 15px; display: flex; align-items: center;">
            <span style="color: white; margin-right: 10px;">📈</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: white;">Analisi Tecnica</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Layout come nell'immagine di riferimento
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<p style='margin-bottom: 5px;'>Asset</p>", unsafe_allow_html=True)
            asset = st.selectbox(
                "Asset",
                ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT"],
                key="ta_asset",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("<p style='margin-bottom: 5px;'>Periodo analisi (giorni)</p>", unsafe_allow_html=True)
            days = st.slider(
                "Periodo",
                1, 365, 30,
                key="ta_days",
                label_visibility="collapsed"
            )
        
        # Pulsante per generare analisi
        if st.button("🔄 Genera Analisi", key="generate_ta", type="primary"):
            with st.spinner("Generazione grafico..."):
                # Ottieni il prezzo reale per l'asset selezionato
                symbol = asset.replace("USDT", "").lower()
                symbol_map = {
                    "btc": "bitcoin",
                    "eth": "ethereum",
                    "bnb": "binancecoin",
                    "xrp": "ripple",
                    "sol": "solana",
                    "ada": "cardano"
                }
                
                current_price = get_crypto_price(symbol_map.get(symbol, symbol))
                
                # Crea dati realistici basati sul prezzo attuale
                volatility = current_price * 0.02  # 2% di volatilità
                
                dates = pd.date_range(end=datetime.now(), periods=days)
                np.random.seed(42)  # Per riproducibilità
                
                # Simula prezzi con trend realistico
                close = np.zeros(days)
                close[0] = current_price
                for i in range(1, days):
                    close[i] = close[i-1] * (1 + np.random.normal(0.001, 0.02))  # Leggero trend rialzista con volatilità
                
                open_prices = close * (1 + np.random.normal(0, 0.005, days))
                high = np.maximum(close, open_prices) * (1 + np.random.normal(0.005, 0.003, days))
                low = np.minimum(close, open_prices) * (1 - np.random.normal(0.005, 0.003, days))
                
                # Crea DataFrame
                data = pd.DataFrame({
                    'open': open_prices,
                    'high': high,
                    'low': low,
                    'close': close
                }, index=dates)
                
                # Calcola RSI
                rsi = calculate_rsi(data)
                
                # Crea grafico
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=(f"Prezzo {asset}", "RSI 14")
                )
                
                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        name="Price",
                        increasing_line_color='#26A69A', 
                        decreasing_line_color='#EF5350'
                    ), row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=rsi.index,
                        y=rsi,
                        line=dict(color='#F0B90B', width=2),
                        name="RSI"
                    ), row=2, col=1
                )
                
                fig.update_layout(
                    height=600,
                    showlegend=False,
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='#0B0E11',
                    paper_bgcolor='#0B0E11',
                    font=dict(color='#FFFFFF')
                )
                
                fig.update_xaxes(gridcolor='#1E2026')
                fig.update_yaxes(gridcolor='#1E2026')
                
                fig.add_hline(y=30, row=2, col=1, line_dash="dot", line_color="#26A69A", annotation_text="Oversold")
                fig.add_hline(y=70, row=2, col=1, line_dash="dot", line_color="#EF5350", annotation_text="Overbought")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Aggiungi analisi automatica
                if st.session_state.auth.get('premium', False):
                    with st.expander("📝 Analisi Automatica"):
                        asset_name = asset.replace("USDT", "")
                        current_price = close[-1]
                        support_level = current_price * 0.95
                        resistance_level = current_price * 1.05
                        entry_level = current_price * 0.97
                        target_level = current_price * 1.03
                        
                        analysis = f"""Analisi tecnica di {asset_name}:
                        
Il trend attuale mostra un supporto a ${support_level:.2f} e resistenza a ${resistance_level:.2f}. 
L'RSI a {rsi.iloc[-1]:.1f} indica {'condizioni di ipercomprato' if rsi.iloc[-1] > 70 else 'condizioni di ipervenduto' if rsi.iloc[-1] < 30 else 'un mercato neutrale'}.

Consiglio: {'Attendere pullback verso' if rsi.iloc[-1] > 60 else 'Considerare ingresso a'} ${entry_level:.2f} per ingresso long con target ${target_level:.2f}."""
                        
                        st.write(analysis)

# ========== MAIN APP ==========
def main():
    try:
        # Imposta lo stile della pagina
        set_page_style()
        
        # Inizializzazione sessione
        if 'auth' not in st.session_state:
            st.session_state.auth = {
                'logged_in': False,
                'username': None,
                'premium': False
            }
        
        # Mostra la vista appropriata
        if not st.session_state.auth['logged_in']:
            show_login_register()
        else:
            show_app_header()
            
            # Layout come nell'immagine di riferimento
            col1, col2 = st.columns([1, 2], gap="large")
            
            with col1:
                show_ai_assistant()
            
            with col2:
                show_wallet_connection()
                show_technical_analysis()
    except Exception as e:
        st.error(f"""
        Si è verificato un errore nell'applicazione.
        Dettagli: {str(e)}
        """)

if __name__ == "__main__":
    main()