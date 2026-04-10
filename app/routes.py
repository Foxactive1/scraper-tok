"""
routes.py — InNovaIdeia / TikTok Scraper Pro
Blueprint Flask com as rotas da API.

Novidade:
  - POST /download  → obtém link direto para download via tikwm.com API
                      (sem marca d'água, sem cookies TikTok)
"""

import logging
from flask import Blueprint, request, jsonify, render_template
from app.tasks import celery, scrape_task
from app.scraper import get_download_url

logger = logging.getLogger(__name__)
api = Blueprint("api", __name__)

ALLOWED_DOMAINS = ("tiktok.com", "vt.tiktok.com", "vm.tiktok.com")


def _is_valid_tiktok_url(url: str) -> bool:
    """Verifica se a URL pertence ao domínio TikTok."""
    if not url.startswith(("http://", "https://")):
        return False
    return any(domain in url for domain in ALLOWED_DOMAINS)


@api.route("/scrape", methods=["POST"])
def scrape():
    """
    POST /scrape
    Body JSON: { "url": "https://vt.tiktok.com/..." }
    Returns: { "task_id": "...", "status": "processing" }
    """
    data = request.get_json(silent=True)

    if not data or not data.get("url"):
        return jsonify({"error": "Campo 'url' é obrigatório"}), 400

    url = data["url"].strip()

    if not _is_valid_tiktok_url(url):
        return jsonify({"error": "URL inválida. Informe uma URL do TikTok válida."}), 400

    task = scrape_task.delay(url)
    logger.info(f"[scrape] task_id={task.id} | url={url}")

    return jsonify({"task_id": task.id, "status": "processing"}), 202


@api.route("/status/<task_id>")
def status(task_id: str):
    """GET /status/<task_id> — retorna estado da task Celery."""
    task = celery.AsyncResult(task_id)

    error_msg   = str(task.result)  if task.failed()     else None
    result_data = task.result       if task.successful() else None

    return jsonify({
        "status": task.status,
        "result": result_data,
        "error":  error_msg,
    })


@api.route("/download", methods=["POST"])
def download():
    """
    POST /download
    Body JSON: { "url": "https://www.tiktok.com/@user/video/123..." }

    Consulta tikwm.com e retorna links diretos para download do vídeo.

    Returns:
        200: {
            "url_sd":  "link sem marca d'água (SD)",
            "url_hd":  "link sem marca d'água (HD, se disponível)",
            "url_wm":  "link com marca d'água"
        }
        400/502: { "error": "mensagem" }
    """
    data = request.get_json(silent=True)

    if not data or not data.get("url"):
        return jsonify({"error": "Campo 'url' é obrigatório"}), 400

    url = data["url"].strip()

    if not _is_valid_tiktok_url(url):
        return jsonify({"error": "URL inválida. Informe uma URL do TikTok válida."}), 400

    try:
        links = get_download_url(url)
        logger.info(f"[download] Links obtidos para: {url}")
        return jsonify(links)
    except Exception as e:
        logger.error(f"[download] Erro ao obter links: {e}")
        return jsonify({"error": f"Não foi possível obter o link de download: {e}"}), 502


@api.route("/")
def index():
    return render_template("index.html")


@api.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Rota não encontrada"}), 404


@api.errorhandler(500)
def internal_error(e):
    msg = str(e)
    logger.error(f"[routes] Erro interno: {msg}")
    return jsonify({"error": f"Erro interno: {msg}"}), 500
