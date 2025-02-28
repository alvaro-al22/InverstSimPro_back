# controllers/market_controller.py
import yfinance as yf
from flask import Blueprint, request, jsonify
import time

market_bp = Blueprint('market', __name__)

# Mapeo de categorías a tickers (puedes extenderlo o actualizarlo según tus necesidades)
TICKER_MAP = {
    'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
    'indices': ['^GSPC', '^NDX', '^DJI'],  # Ejemplo: S&P 500, NASDAQ 100, Dow Jones
    'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD']
}

@market_bp.route('/assets', methods=['GET'])
def get_assets():
    category = request.args.get('category')
    if category not in TICKER_MAP:
        return jsonify({"error": "Categoría no válida"}), 400

    tickers = TICKER_MAP[category]
    assets = []
    for ticker in tickers:
        tkr = yf.Ticker(ticker)
        attempts = 0
        info = None
        # Reintenta hasta 3 veces en caso de error
        while attempts < 3:
            try:
                info = tkr.info
                break
            except Exception as e:
                attempts += 1
                print(f"Error obteniendo info para {ticker}: {e}. Intento {attempts}/3")
                time.time.sleep(2)  # Espera 2 segundos antes de reintentar

        if not info:
            # Si aún no se obtuvo info, se omite este ticker
            continue

        current_price = info.get('regularMarketPrice')
        previous_close = info.get('previousClose')
        change = None
        if current_price is not None and previous_close:
            change_percent = ((current_price - previous_close) / previous_close) * 100
            change = f"{change_percent:.1f}%"
        assets.append({
            "id": ticker,
            "name": info.get('shortName') or ticker,
            "price": f"{current_price:.2f}" if current_price else "N/A",
            "change": change if change else "N/A"
        })

    return jsonify(assets), 200

@market_bp.route('/simulation', methods=['POST'])
def simulate_investment():
    """
    Simula una inversión usando datos históricos reales.
    Se espera recibir:
      - amount: cantidad invertida (número)
      - startDate: fecha de inicio (YYYY-MM-DD)
      - endDate: fecha final (YYYY-MM-DD)
      - selectedAssets: lista de tickers (por ejemplo, ["AAPL", "GOOGL"])
    """
    data = request.get_json()
    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Cantidad inválida"}), 400

    start_date = data.get('startDate')
    end_date = data.get('endDate')
    selected_assets = data.get('selectedAssets', [])

    if not start_date or not end_date or not selected_assets:
        return jsonify({"error": "Faltan parámetros"}), 400

    simulation_results = []
    for ticker in selected_assets:
        # Descargar datos históricos usando yfinance
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            continue  # Si no hay datos, se omite este activo

        initial_price = df.iloc[0]['Close']
        final_price = df.iloc[-1]['Close']
        shares = amount / initial_price
        final_value = shares * final_price
        profit = final_value - amount
        return_percentage = (profit / amount) * 100

        simulation_results.append({
            "ticker": ticker,
            "initial_price": initial_price,
            "final_price": final_price,
            "final_value": final_value,
            "profit": profit,
            "return_percentage": return_percentage
        })

    return jsonify({"results": simulation_results}), 200
