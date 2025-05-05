import streamlit as st
import json
import os
import requests
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from pycoingecko import CoinGeckoAPI
from binance.client import Client
from dotenv import load_dotenv
from datetime import datetime
from cryptography.fernet import Fernet
import openai
import locale

# =============================================
# FUNZIONE PERSONALIZZATA RSI
# =============================================
def calculate_rsi(data, window=14):
    """Calcola l'RSI senza librerie esterne"""
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    ema_up = up.ewm(span=window, adjust=False).mean()
    ema_down = down.ewm(span=window, adjust=False).mean()
    
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

# =============================================
# CONFIGURAZIONE INIZIALE
# =============================================
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
cg = CoinGeckoAPI()

# Configurazione percorsi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

USER_FILE = os.path.join(DATA_DIR, "users.json")
SECURE_KEY_FILE = os.path.join(DATA_DIR, "secure_keys.json")
FERNET_KEY_FILE = os.path.join(DATA_DIR, "fernet.key")
LOGO_PATH = os.path.join(ASSETS_DIR, "trademate-logo.png")

# =============================================
# FUNZIONI DI SICUREZZA
# =============================================
def get_or_create_fernet_key():
    if not os.path.exists(FERNET_KEY_FILE):
        key = Fernet.generate_key()
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    with open(FERNET_KEY_FILE, "rb") as f:
        return Fernet(f.read())

def save_api_keys(api_key, api_secret):
    fernet = get_or_create_fernet_key()
    encrypted = {
        "api_key": fernet.encrypt(api_key.encode()).decode(),
        "api_secret": fernet.encrypt(api_secret.encode()).decode()
    }
    with open(SECURE_KEY_FILE, "w") as f:
        json.dump(encrypted, f)

def load_api_keys():
    if not os.path.exists(SECURE_KEY_FILE):
        return None, None
    fernet = get_or_create_fernet_key()
    with open(SECURE_KEY_FILE, "r") as f:
        data = json.load(f)
        return (
            fernet.decrypt(data["api_key"].encode()).decode(),
            fernet.decrypt(data["api_secret"].encode()).decode()
        )

# =============================================
# GESTIONE UTENTI
# =============================================
def load_users():
    try:
        if not os.path.exists(USER_FILE):
            with open(USER_FILE, "w") as f:
                json.dump({}, f)
            return {}
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Errore caricamento utenti: {str(e)}")
        return {}

def save_users(users):
    try:
        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio utenti: {str(e)}")
        return False

# =============================================
# FUNZIONI BINANCE
# =============================================
def get_binance_client():
    api_key, api_secret = load_api_keys()
    if not api_key or not api_secret:
        return None
    
    try:
        client = Client(api_key, api_secret)
        client.get_account()
        return client
    except Exception as e:
        st.error(f"Errore connessione Binance: {str(e)}")
        return None

def get_wallet_data(client):
    ASSET_MAP = {
        "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
        "USDT": "tether", "USDC": "usd-coin", "SOL": "solana",
        "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin"
    }
    
    try:
        balances = client.get_account()['balances']
        wallet = {}
        for asset in balances:
            if float(asset['free']) > 0:
                symbol = asset['asset']
                gecko_id = ASSET_MAP.get(symbol, symbol.lower())
                prices = cg.get_price(ids=gecko_id, vs_currencies=['usd'])
                if gecko_id in prices:
                    wallet[symbol] = {
                        'quantity': float(asset['free']),
                        'usd_value': float(asset['free']) * prices[gecko_id]['usd']
                    }
        return wallet
    except Exception as e:
        st.error(f"Errore lettura wallet: {str(e)}")
        return {}

# =============================================
# INTERFACCIA UTENTE
# =============================================
def init_session():
    if 'logged_in' not in st.session_state:
        st.session_state.update({
            'logged_in': False,
            'username': '',
            'wallet': {},
            'client': None,
            'manual_wallet': {},
            'question_count': 0,
            'premium': False
        })

def show_auth_section():
    st.title("🔐 Accesso TradeMate")
    
    tab1, tab2 = st.tabs(["Login", "Registrazione"])
    
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            
            if st.form_submit_button("Accedi"):
                users = load_users()
                if user in users and users[user]['password'] == pwd:
                    st.session_state.update({
                        'logged_in': True,
                        'username': user,
                        'premium': users[user].get('premium', False)
                    })
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
    
    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("Nuovo username")
            new_pwd = st.text_input("Nuova password", type="password")
            confirm_pwd = st.text_input("Conferma password", type="password")
            
            if st.form_submit_button("Crea account"):
                if new_pwd != confirm_pwd:
                    st.warning("Le password non coincidono")
                else:
                    users = load_users()
                    if new_user in users:
                        st.warning("Username già esistente")
                    else:
                        users[new_user] = {'password': new_pwd, 'premium': False}
                        save_users(users)
                        st.success("Account creato! Ora puoi accedere")

def manual_wallet_form():
    st.subheader("📥 Inserisci criptovalute manualmente")
    crypto_options = {
        "BTC": "bitcoin", "ETH": "ethereum", "XRP": "ripple",
        "BNB": "binancecoin", "SOL": "solana", "ADA": "cardano",
        "DOGE": "dogecoin", "USDT": "tether", "USDC": "usd-coin"
    }
    
    selected = st.selectbox("Criptovaluta", list(crypto_options.keys()))
    quantity = st.number_input("Quantità", min_value=0.0, format="%f")
    
    if st.button("Aggiungi al Wallet"):
        gecko_id = crypto_options.get(selected, selected.lower())
        try:
            price_data = cg.get_price(ids=gecko_id, vs_currencies=['usd'])
            if gecko_id in price_data:
                st.session_state.manual_wallet[selected] = {
                    'quantity': quantity,
                    'usd_value': quantity * price_data[gecko_id]['usd']
                }
                st.success(f"{selected} aggiunto al wallet!")
            else:
                st.error("Impossibile ottenere il prezzo per questa valuta")
        except Exception as e:
            st.error(f"Errore: {str(e)}")

def main_interface():
    st.title(f"💰 Portfolio - {st.session_state.username}")
    
    if st.button("🔒 Logout"):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Sezione Wallet
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("🔑 Configurazione")
        mode = st.radio("Modalità", ["Manuale", "API Binance"])
        
        if mode == "Manuale":
            manual_wallet_form()
            wallet = st.session_state.manual_wallet
        else:
            api_key = st.text_input("API Key", type="password")
            api_secret = st.text_input("API Secret", type="password")
            
            if st.button("Connetti a Binance"):
                if api_key and api_secret:
                    save_api_keys(api_key, api_secret)
                    st.success("Chiavi salvate correttamente!")
            
            client = get_binance_client()
            wallet = get_wallet_data(client) if client else {}
        
        # Assistente AI
        st.markdown("---")
        st.subheader("🤖 Assistente AI")
        question = st.text_input("Fai una domanda sulle criptovalute")
        
        if st.button("Chiedi all'AI"):
            if st.session_state.premium:
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Sei un esperto assistente di criptovalute."},
                            {"role": "user", "content": question}
                        ]
                    )
                    st.success(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Errore AI: {str(e)}")
            elif st.session_state.question_count < 3:
                st.info("Risposta demo: Attiva Premium per risposte complete")
                st.session_state.question_count += 1
            else:
                st.warning("Limite gratuito raggiunto. Attiva Premium.")
    
    with col2:
        if wallet:
            st.subheader("📊 Il tuo Wallet")
            df = pd.DataFrame.from_dict(wallet, orient='index')
            st.dataframe(df.style.format({
                'quantity': '{:.6f}',
                'usd_value': '${:,.2f}'
            }))
            
            # Grafico prezzi
            selected = st.selectbox("Seleziona asset", list(wallet.keys()))
            try:
                data = cg.get_coin_market_chart_by_id(
                    id=selected.lower(), 
                    vs_currency='usd', 
                    days=30
                )
                prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
                prices['date'] = pd.to_datetime(prices['timestamp'], unit='ms')
                
                # Calcola RSI con la nostra funzione
                prices['RSI'] = calculate_rsi(prices['price'], window=14)
                
                # Grafico prezzo
                fig_price = go.Figure(
                    go.Scatter(x=prices['date'], y=prices['price'], name='Prezzo USD')
                )
                st.plotly_chart(fig_price.update_layout(title=f"Andamento {selected}"))
                
                # Grafico RSI
                fig_rsi = go.Figure(
                    go.Scatter(x=prices['date'], y=prices['RSI'], name='RSI (14 giorni)')
                )
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                st.plotly_chart(fig_rsi.update_layout(title="Indice di Forza Relativa (RSI)"))
                
            except Exception as e:
                st.warning(f"Dati non disponibili: {str(e)}")

# =============================================
# AVVIO APPLICAZIONE
# =============================================
if __name__ == "__main__":
    st.set_page_config(
        page_title="TradeMate",
        layout="wide",
        page_icon="💰"
    )
    
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)
    
    init_session()
    
    if not st.session_state.logged_in:
        show_auth_section()
    else:
        main_interface()