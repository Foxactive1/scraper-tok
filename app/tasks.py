"""
tasks.py — InNovaIdeia / TikTok Scraper Pro
Celery task definitions — modo compatível com Pydroid 3 / Android.

Ambiente Android (Pydroid 3 / Termux):
  - Redis NÃO roda nativamente no Android sem root.
  - Solução: task_always_eager=True + backend cache+memory://
    → Task executa SINCRONAMENTE dentro do processo Flask.
    → Sem necessidade de Redis, worker ou broker externos.
  - O frontend continua fazendo polling normalmente (compatível).

Ambiente produção (Linux/Docker com Redis):
  - Definir CELERY_TASK_ALWAYS_EAGER=false e REDIS_URL corretamente.
"""

import os
import logging
from celery import Celery
from config import Config
from app.scraper import resolve_url, fetch_html, extract_json, parse_video

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Detecta modo de execução via env var
# Padrão: True (Pydroid 3 / Android — sem Redis)
# Produção com Redis: export CELERY_TASK_ALWAYS_EAGER=false
# ------------------------------------------------------------------
_always_eager = os.getenv("CELERY_TASK_ALWAYS_EAGER", "true").lower() == "true"

_broker  = "memory://"       if _always_eager else Config.REDIS_URL
_backend = "cache+memory://" if _always_eager else Config.REDIS_URL

celery = Celery(__name__, broker=_broker, backend=_backend)

celery.conf.update(
    task_always_eager=_always_eager,
    task_store_eager_result=True,

    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Evita crash ao iniciar sem Redis disponível
    broker_connection_retry_on_startup=False,

    result_expires=3600,
)

if _always_eager:
    logger.warning(
        "[tasks] Modo EAGER ativo — sem Redis (Pydroid 3/Android). "
        "Para produção, defina CELERY_TASK_ALWAYS_EAGER=false."
    )


@celery.task(bind=True, max_retries=3)
def scrape_task(self, url: str) -> dict:
    """
    Task Celery para scraping de um vídeo TikTok.

    Modo eager (Android): executa sincronamente na thread do Flask.
    Produção: executado pelo worker de forma assíncrona.

    Args:
        url: URL do vídeo TikTok (link curto ou completo)

    Returns:
        dict com id, desc, author, likes, views, video_url
    """
    try:
        logger.info(f"[scrape_task] Iniciando | URL: {url} | Tentativa: {self.request.retries + 1}")

        final_url = resolve_url(url)
        logger.info(f"[scrape_task] URL resolvida: {final_url}")

        html = fetch_html(final_url)
        logger.info(f"[scrape_task] HTML obtido: {len(html)} bytes")

        data = extract_json(html)
        if not data:
            raise ValueError("JSON '__UNIVERSAL_DATA_FOR_REHYDRATION__' não encontrado no HTML")

        parsed = parse_video(data)
        if not parsed:
            raise ValueError("Falha ao extrair dados — estrutura JSON inesperada")

        logger.info(f"[scrape_task] Concluído | video_id: {parsed.get('id')}")
        return parsed

    except Exception as exc:
        logger.error(f"[scrape_task] Erro (tentativa {self.request.retries + 1}): {exc}")

        if self.request.retries >= self.max_retries:
            logger.error("[scrape_task] Max retries atingido. Abortando.")
            raise exc

        raise self.retry(exc=exc, countdown=5)
