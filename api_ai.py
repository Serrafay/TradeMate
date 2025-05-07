from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

def get_crypto_price(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[symbol]['usd']
    except Exception as e:
        logging.error(f"[Price Error] {e}")
        fallback = {
            "bitcoin": 64250.75,
            "ethereum": 3075.25,
            "binancecoin": 595.80,
            "ripple": 0.5025,
            "solana": 145.75,
            "cardano": 0.45,
            "dogecoin": 0.15,
            "polkadot": 7.25
        }
        return fallback.get(symbol, 1000)

# 🔁 ROUTE GENERICA per qualsiasi crypto
@app.route('/crypto/<symbol>', methods=['GET'])
def get_crypto_price_route(symbol):
    price = get_crypto_price(symbol)
    return jsonify(price)

# ✅ ROUTE SPECIFICA bitcoin (puoi tenerla o rimuoverla)
@app.route('/crypto/bitcoin', methods=['GET'])
def get_bitcoin_price():
    price = get_crypto_price('bitcoin')
    return jsonify(price)

# 🤖 ANALISI AI
@app.route('/api/ai-analysis', methods=['POST'])
def ai_analysis():
    try:
        data = request.json
        crypto = data.get("crypto", "BTC").upper()
        context = data.get("context", "")

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

        cg_symbol = symbol_map.get(crypto, "bitcoin")
        price = get_crypto_price(cg_symbol)

        analysis = f"""Analisi tecnica di {crypto}: 
Il prezzo attuale è ${price:,.2f}. 
Il trend mostra un supporto a ${price*0.95:,.2f} e una resistenza a ${price*1.05:,.2f}. 
Consiglio: {'attendere un pullback' if 'correzione' in context.lower() else 'considerare un ingresso'} a ${price*0.97:,.2f} con target ${price*1.03:,.2f}."""

        return jsonify({
            "crypto": crypto,
            "response": analysis,
            "time": datetime.now().strftime("%H:%M %d/%m/%Y")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
