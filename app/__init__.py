from flask import Flask
from app.routes import api
import logging

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api)
    
    # Configura logging para saída no console
    logging.basicConfig(level=logging.INFO)
    
    return app