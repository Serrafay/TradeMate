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

import streamlit as st
import json
import os
import requests
import plotly.graph_objs as go
import pandas as pd
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
