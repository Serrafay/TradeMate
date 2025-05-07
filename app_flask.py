from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

def get_crypto_price(symbol: str) -> float:
    """Ottiene il prezzo aggiornato della crypto da CoinGecko (USD)"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[symbol]['usd']
    except:
        return 0.0

def get_usd_to_eur_rate() -> float:
    """Ottiene il tasso di cambio USD → EUR"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['rates']['EUR']
    except:
        return 0.92  # fallback di emergenza

@app.route('/api/ai-analysis', methods=['POST'])
def ai_analysis():
    data = request.get_json()
    crypto = data.get('crypto', 'BTC').upper()
    context = data.get('context', '')

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

    if crypto not in symbol_map:
        return jsonify({"error": "Simbolo non supportato"}), 400

    symbol = symbol_map[crypto]
    price_usd = get_crypto_price(symbol)

    if price_usd == 0.0:
        return jsonify({"error": "Prezzo non disponibile"}), 503

    # Ottieni il tasso di cambio USD → EUR
    usd_to_eur = get_usd_to_eur_rate()
    price_eur = price_usd * usd_to_eur

    support_usd = price_usd * 0.95
    resistance_usd = price_usd * 1.05
    entry_usd = price_usd * 0.97
    target_usd = price_usd * 1.03

    support_eur = support_usd * usd_to_eur
    resistance_eur = resistance_usd * usd_to_eur
    entry_eur = entry_usd * usd_to_eur
    target_eur = target_usd * usd_to_eur

    analysis_text = (
        f"Analisi tecnica di {crypto}: "
        f"Prezzo attuale ${price_usd:,.2f} (~€{price_eur:,.2f}). "
        f"Supporto ${support_usd:,.2f} (~€{support_eur:,.2f}), resistenza ${resistance_usd:,.2f} (~€{resistance_eur:,.2f}). "
        f"Ingresso consigliato a ${entry_usd:,.2f} (~€{entry_eur:,.2f}), target ${target_usd:,.2f} (~€{target_eur:,.2f})."
    )

    response = {
        "crypto": crypto,
        "context": context,
        "usd_to_eur_rate": usd_to_eur,
        "price_usd": price_usd,
        "price_eur": price_eur,
        "support_usd": support_usd,
        "support_eur": support_eur,
        "resistance_usd": resistance_usd,
        "resistance_eur": resistance_eur,
        "entry_usd": entry_usd,
        "entry_eur": entry_eur,
        "target_usd": target_usd,
        "target_eur": target_eur,
        "response": analysis_text,
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
