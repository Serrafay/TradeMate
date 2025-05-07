<<<<<<< HEAD
# Modifica del 6 maggio 2025  # ✅ Modifica test 6 maggio 2025


import streamlit as st
=======
import streamlit as st
# TradeMate - app_streamlit.py COMPLETO
# ----------------- Header con logo -------------------
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 20px;'>
        <img src='assets/trademate-logo.png' alt='TradeMate Logo' width='100'/>
        <h1 style='margin-top: 0;'>🚀 TradeMate</h1>
        <h4>La tua dashboard per il trading cripto</h4>
    </div>
    """,
    unsafe_allow_html=True
)


>>>>>>> a0e5bef88f313569822f2b9c0563e3f45ca81cf4
import json
import os
import requests
import plotly.graph_objs as go
import pandas as pd
<<<<<<< HEAD
from ta.momentum import RSIIndicator
from pycoingecko import CoinGeckoAPI
from binance.client import Client
from dotenv import load_dotenv
from datetime import datetime
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Global config
cg = CoinGeckoAPI()
USER_FILE = "data/users.json"
MANUAL_WALLET_FILE = "data/manual_wallet.json"
SECURE_KEY_FILE = "data/secure_keys.json"
FERNET_KEY_FILE = "data/fernet.key"

st.set_page_config(page_title="TradeMate", layout="wide")

# --- Security ---
def get_or_create_fernet_key():
    if not os.path.exists(FERNET_KEY_FILE):
        os.makedirs(os.path.dirname(FERNET_KEY_FILE), exist_ok=True)
        key = Fernet.generate_key()
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

def save_api_keys(api_key, api_secret):
    f = get_or_create_fernet_key()
    data = {
        "api_key": f.encrypt(api_key.encode()).decode(),
        "api_secret": f.encrypt(api_secret.encode()).decode()
    }
    with open(SECURE_KEY_FILE, "w") as f_out:
        json.dump(data, f_out)

def load_api_keys():
    if not os.path.exists(SECURE_KEY_FILE):
        return None, None
    f = get_or_create_fernet_key()
    with open(SECURE_KEY_FILE, "r") as f_in:
        data = json.load(f_in)
        return f.decrypt(data["api_key"].encode()).decode(), f.decrypt(data["api_secret"].encode()).decode()

# --- User management ---
def load_users():
    if not os.path.exists(USER_FILE):
        os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrati"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login effettuato")
                st.rerun()
            else:
                st.error("Credenziali errate")

    with tab2:
        new_user = st.text_input("Crea username")
        new_pass = st.text_input("Crea password", type="password")
        if st.button("Registrati"):
            if new_user in users:
                st.warning("Utente già esistente")
            else:
                users[new_user] = {"password": new_pass}
                save_users(users)
                st.success("Registrazione completata. Accedi ora!")

# --- Wallet Binance ---
def get_wallet_from_binance(client):
    id_mapping = {
        "BUSD": "binance-usd",
        "USDT": "tether",
        "USDC": "usd-coin",
        "TUSD": "true-usd",
        "FDUSD": "first-digital-usd",
        "XRP": "ripple"
    }

    try:
        account = client.get_account()
        balances = account.get("balances", [])
        wallet = {}

        filtered_balances = [
            b for b in balances
            if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0
        ]

        for b in filtered_balances[:10]:
            asset = b["asset"]
            qty = float(b.get("free", 0))
            try:
                gecko_id = id_mapping.get(asset.upper(), asset.lower())
                price_data = cg.get_price(ids=gecko_id, vs_currencies=["usd", "eur"])
                usd_price = price_data.get(gecko_id, {}).get("usd", 0)
                eur_price = price_data.get(gecko_id, {}).get("eur", 0)
                if usd_price > 0:
                    wallet[asset] = {
                        "quantity": qty,
                        "usd_value": qty * usd_price,
                        "eur_value": qty * eur_price
                    }
            except:
                pass
        return wallet
    except Exception as e:
        st.error(f"Errore Binance: {e}")
        return {}

# --- Manual Wallet Entry ---
def manual_wallet_form():
    st.subheader("📥 Inserisci criptovalute manualmente")
    crypto_options = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "XRP": "ripple",
        "BNB": "binancecoin",
        "SOL": "solana",
        "ADA": "cardano",
        "DOGE": "dogecoin"
    }

    selected = st.selectbox("Scegli una criptovaluta dal menu", list(crypto_options.keys()))
    manual_input = st.text_input("Oppure inserisci manualmente la sigla della cripto", "")
    quantity = st.number_input("Quantità", min_value=0.0, step=0.00000001, format="%f")

    if st.button("Aggiungi"):
        coin_symbol = manual_input.strip().upper() if manual_input else selected
        gecko_id = crypto_options.get(coin_symbol.upper(), coin_symbol.lower())
        try:
            price_data = cg.get_price(ids=gecko_id, vs_currencies=["usd", "eur"])
            usd = price_data[gecko_id]["usd"]
            eur = price_data[gecko_id]["eur"]
            wallet = {
                coin_symbol: {
                    "quantity": quantity,
                    "usd_value": quantity * usd,
                    "eur_value": quantity * eur
                }
            }
            st.session_state.manual_wallet = wallet
        except:
            st.error("Errore nel recupero del prezzo della criptovaluta.")

# --- UI After Login ---
if st.session_state.logged_in:
    st.title("👋 TradeMate Dashboard")

    mode = st.radio("Come vuoi caricare il tuo wallet?", ["Manuale", "API Binance"])
    wallet = {}

    if mode == "Manuale":
        manual_wallet_form()
        wallet = st.session_state.get("manual_wallet", {})

    else:
        st.subheader("🔐 Inserisci le tue chiavi API Binance")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        if st.button("Salva e connetti"):
            save_api_keys(api_key, api_secret)
            st.success("Chiavi salvate. Ricarica la pagina per vedere il wallet.")

        api_key, api_secret = load_api_keys()
        if api_key and api_secret:
            client = Client(api_key, api_secret)
            wallet = get_wallet_from_binance(client)

    st.subheader("📊 Il tuo Wallet")
    if wallet:
        df_wallet = pd.DataFrame(wallet).T
        st.dataframe(df_wallet)

        # Selezione cripto per grafici
        selected_coin = st.selectbox("Scegli una cripto per vedere i grafici", list(wallet.keys()))
        id_mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "XRP": "ripple",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BUSD": "binance-usd",
            "TUSD": "true-usd",
            "FDUSD": "first-digital-usd"
        }
        coin_id = id_mapping.get(selected_coin.upper(), selected_coin.lower())
        try:
            data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency='usd', days=30)
            df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("date", inplace=True)
            df["RSI"] = RSIIndicator(df["price"], window=14).rsi()

            st.plotly_chart(go.Figure(go.Scatter(x=df.index, y=df["price"], name="Prezzo USD")).update_layout(title="Andamento prezzo"))
            st.plotly_chart(go.Figure(go.Scatter(x=df.index, y=df["RSI"], name="RSI")
                            ).add_hline(y=70, line_color="red", line_dash="dot")
                            .add_hline(y=30, line_color="green", line_dash="dot")
                            .update_layout(title="RSI"))
        except:
            st.warning("Grafico non disponibile per questa moneta.")

    # News + AI Suggestion
    st.subheader("📰 Notizie recenti + Consiglio AI")
    try:
        api_key_news = os.getenv("NEWSDATA_API_KEY")
        news = requests.get(f"https://newsdata.io/api/1/news?apikey={api_key_news}&q=cryptocurrency&language=en").json()
        articles = news.get("results", [])[:5]
        score = 0
        for article in articles:
            title = article.get("title", "").lower()
            st.markdown(f"**{article['title']}**")
            st.caption(article.get("description", ""))
            if any(x in title for x in ["bullish", "surge", "buy"]):
                score += 1
            elif any(x in title for x in ["crash", "bearish", "sell"]):
                score -= 1

        if score > 1:
            st.success("🤖 AI suggerisce: Compra")
        elif score < -1:
            st.error("🤖 AI suggerisce: Vendi")
        else:
            st.info("🤖 AI suggerisce: Mantieni")

    except:
        st.warning("Impossibile recuperare notizie al momento.")

=======
import numpy as np
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
import pyrebase

# ----------------- CONFIG -------------------
st.set_page_config(page_title="TradeMate", layout="wide")
load_dotenv()

# Firebase Config
firebase_config = json.loads(os.getenv("FIREBASE_CONFIG_JSON", "{}"))
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# ----------------- Login -------------------
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.rerun()
            except:
                st.error("Credenziali non valide")

def logout():
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

if not st.session_state.user:
    st.title("TradeMate - Login")
    login()
    st.stop()

# ----------------- UI Header -------------------
st.markdown("""
    <h1 style='text-align: center;'>🚀 TradeMate</h1>
    <h4 style='text-align: center;'>La tua dashboard per il trading cripto</h4>
""", unsafe_allow_html=True)
logout()

# ----------------- Modalità -------------------
mode = st.sidebar.radio("Modalità", ["Manuale", "API Binance"])
st.session_state.wallet = st.session_state.get("wallet", {})

if mode == "Manuale":
    st.sidebar.markdown("### Inserisci criptovalute manualmente")
    crypto = st.sidebar.selectbox("Criptovaluta", ["BTC", "ETH", "SOL", "BNB", "XRP"])
    quantity = st.sidebar.number_input("Quantità", min_value=0.0, value=0.0, step=0.1)
    if st.sidebar.button("Aggiungi al Wallet"):
        st.session_state.wallet[crypto] = st.session_state.wallet.get(crypto, 0) + quantity
        st.success(f"{crypto} aggiunto al wallet!")

elif mode == "API Binance":
    st.sidebar.markdown("### 🔗 Connettiti al wallet Binance")
    if BINANCE_API_KEY and BINANCE_API_SECRET:
        from binance.client import Client
        client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        account = client.get_account()
        balances = account["balances"]
        st.session_state.wallet = {b["asset"]: float(b["free"]) for b in balances if float(b["free"]) > 0}
    else:
        st.warning("Chiavi Binance non configurate.")

# ----------------- Assistente AI -------------------
st.markdown("### 🤖 Assistente AI")
question = st.text_input("Fai una domanda sulle criptovalute")
if question and OPENAI_API_KEY:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    if response.status_code == 200:
        ai_response = response.json()["choices"][0]["message"]["content"]
        st.write(ai_response)
    else:
        st.error("Errore nella risposta dell'AI")

# ----------------- Portfolio -------------------
st.markdown("### 📊 Il tuo Wallet")
cg = CoinGeckoAPI()
data = []
for symbol, qty in st.session_state.wallet.items():
    try:
        price_data = cg.get_price(ids=symbol.lower(), vs_currencies='usd')
        price = price_data[symbol.lower()]["usd"]
        usd_value = price * qty
        data.append({"symbol": symbol, "quantity": qty, "usd_value": usd_value})
    except:
        data.append({"symbol": symbol, "quantity": qty, "usd_value": "Errore"})

df = pd.DataFrame(data)
st.dataframe(df)

# ----------------- Grafico Prezzo + RSI -------------------
st.markdown("### 📈 Grafico prezzo")
asset = st.selectbox("Seleziona asset", ["bitcoin", "ethereum", "solana"])
try:
    hist = cg.get_coin_market_chart_by_id(id=asset, vs_currency="usd", days=30)
    prices = hist["prices"]
    df_prices = pd.DataFrame(prices, columns=["timestamp", "price"])
    df_prices["timestamp"] = pd.to_datetime(df_prices["timestamp"], unit="ms")

    # RSI
    delta = df_prices["price"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df_prices["RSI"] = rsi

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_prices["timestamp"], y=df_prices["price"], name="Prezzo"))
    fig.add_trace(go.Scatter(x=df_prices["timestamp"], y=df_prices["RSI"], name="RSI", yaxis="y2"))

    fig.update_layout(
        title=f"Prezzo e RSI di {asset.capitalize()}",
        xaxis_title="Data",
        yaxis=dict(title="Prezzo (USD)"),
        yaxis2=dict(title="RSI", overlaying="y", side="right"),
    )
    st.plotly_chart(fig, use_container_width=True)
except:
    st.warning("Errore nel caricamento del grafico.")
>>>>>>> a0e5bef88f313569822f2b9c0563e3f45ca81cf4
