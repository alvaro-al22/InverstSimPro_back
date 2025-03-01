# main.py
from flask import Flask
from flask_cors import CORS
from models import db
from controllers.user_controller import user_bp
from controllers.market_controller import market_bp


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investsim.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Usa variables de entorno en producción

CORS(app)
db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(market_bp, url_prefix='/api/market')

@app.route("/")
def index():
    return "API de InvestSim con datos reales", 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
