# main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)  # habilita peticiones CORS desde tu frontend

# (Opcional) Ejemplo de ruta que devuelva activos "mock" según categoría:
@app.route("/api/assets/<string:category>", methods=["GET"])
def get_assets(category):
    """
    Devuelve una lista de activos ficticios (o reales, si quieres consultarlos
    desde una base de datos o API externa) según la categoría (stocks, indices, crypto).
    """
    mock_assets = {
        "stocks": [
            {"id": "AAPL", "name": "Apple Inc.", "price": "175.43", "change": "+2.3%"},
            {"id": "GOOGL", "name": "Alphabet Inc.", "price": "2789.23", "change": "+1.8%"},
            {"id": "MSFT", "name": "Microsoft Corp.", "price": "334.12", "change": "+1.5%"},
            {"id": "AMZN", "name": "Amazon.com Inc.", "price": "3421.57", "change": "-0.7%"},
        ],
        "indices": [
            {"id": "SPX", "name": "S&P 500", "price": "4532.12", "change": "+1.2%"},
            {"id": "NDX", "name": "NASDAQ 100", "price": "15234.56", "change": "+1.7%"},
            {"id": "DJI", "name": "Dow Jones", "price": "34567.89", "change": "+0.9%"},
        ],
        "crypto": [
            {"id": "BTC", "name": "Bitcoin", "price": "45678.90", "change": "+5.4%"},
            {"id": "ETH", "name": "Ethereum", "price": "3234.56", "change": "+4.2%"},
            {"id": "BNB", "name": "Binance Coin", "price": "412.34", "change": "+2.8%"},
        ],
    }

    assets = mock_assets.get(category, [])
    return jsonify(assets), 200


@app.route("/api/simulate", methods=["POST"])
def simulate_investment():
    """
    Recibe los datos de la simulación (monto, fechas, activos, etc.) 
    y retorna resultados calculados.
    """
    data = request.get_json()

    # Ejemplo de datos que esperaríamos:
    # {
    #   "amount": "1000",
    #   "startDate": "2022-01-01",
    #   "endDate": "2023-01-01",
    #   "reinvestDividends": false,
    #   "riskLevel": "moderate",
    #   "notificationFrequency": "daily",
    #   "selectedAssets": ["AAPL", "GOOGL"],
    #   "simulationType": "finite"  # o "daily"
    # }

    amount = float(data.get("amount", 0))
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    simulation_type = data.get("simulationType", "finite")
    selected_assets = data.get("selectedAssets", [])

    # Aquí podrías hacer consultas reales con yfinance si deseas 
    # datos históricos:
    # Ejemplo => yf.download("AAPL", start="2022-01-01", end="2023-01-01")

    # Para la demo, solo calculamos un "mock" de resultados:
    factor = 1.5  # supongamos que crece 50%
    final_value = amount * factor
    return_percentage = (final_value - amount) / amount * 100
    is_positive = return_percentage >= 0

    # Ejemplo de actualizaciones diarias, si es simulationType="daily"
    daily_updates = None
    if simulation_type == "daily":
        daily_updates = [
            {"date": "2024-05-01", "value": amount * 1.02, "change": "+2.0%"},
            {"date": "2024-05-02", "value": amount * 1.03, "change": "+1.0%"},
            {"date": "2024-05-03", "value": amount * 1.025, "change": "-0.5%"},
        ]

    # Construimos la respuesta final
    response = {
        "initialInvestment": amount,
        "finalValue": final_value,
        "returnPercentage": return_percentage,
        "isPositive": is_positive,
        "simulationType": simulation_type,
        "selectedAssets": selected_assets,
        "recommendations": [
            "Diversifica tu cartera para minimizar riesgos",
            "Considera reinvertir las ganancias",
            "Mantén un horizonte de inversión a largo plazo"
        ],
        "dailyUpdates": daily_updates
    }

    return jsonify(response), 200


@app.route("/")
def index():
    return "API de InvestSim en Flask", 200


if __name__ == "__main__":
    # Ejecuta la app en modo debug (solo en desarrollo)
    app.run(debug=True, port=5000)
