"""
run.py — InNovaIdeia / TikTok Scraper Pro
Entrypoint da aplicação Flask.

Produção (Railway/Docker): usa Gunicorn via startCommand no railway.json
Desenvolvimento local / Pydroid 3: executa com servidor Flask built-in
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Lê $PORT injetado pelo Railway — fallback 5000 para dev local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
