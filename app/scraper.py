"""
scraper.py — InNovaIdeia / TikTok Scraper Pro
Extração HTML, parsing JSON e download via tikwm.com API.

Funções:
  - get_headers()        → headers anti-bot
  - get_proxy()          → proxy aleatório (se configurado)
  - resolve_url(url)     → segue redirecionamentos
  - fetch_html(url)      → obtém HTML da página
  - extract_json(html)   → extrai __UNIVERSAL_DATA_FOR_REHYDRATION__
  - parse_video(data)    → extrai campos do vídeo
  - get_download_url(url)→ obtém links de download via tikwm.com (sem watermark)
"""

import requests
import random
import re
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

# URL da API pública tikwm.com — fornece links diretos sem marca d'água
TIKWM_API = "https://www.tikwm.com/api/"


def get_headers() -> dict:
    """Headers HTTP com User-Agent aleatório para reduzir detecção bot."""
    return {
        "User-Agent": Config.get_random_user_agent(),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
    }


def get_proxy() -> dict | None:
    """Retorna proxy aleatório ou None se não configurado."""
    if Config.PROXIES:
        proxy_url = random.choice(Config.PROXIES)
        return {"http": proxy_url, "https": proxy_url}
    return None


def resolve_url(url: str) -> str:
    """
    Segue redirecionamentos (ex: vt.tiktok.com → URL canônica).

    Raises:
        Exception: se a requisição falhar
    """
    try:
        r = requests.get(
            url,
            headers=get_headers(),
            allow_redirects=True,
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.url
    except requests.RequestException as e:
        raise Exception(f"Erro ao resolver URL '{url}': {e}") from e


def fetch_html(url: str) -> str:
    """
    Obtém HTML da página TikTok com proxy opcional.

    Raises:
        Exception: se a requisição HTTP falhar
    """
    proxies = get_proxy()
    try:
        r = requests.get(
            url,
            headers=get_headers(),
            proxies=proxies,
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        raise Exception(f"Falha ao buscar HTML de '{url}': {e}") from e


def extract_json(html: str) -> dict | None:
    """
    Extrai JSON embutido na tag __UNIVERSAL_DATA_FOR_REHYDRATION__.

    Returns:
        dict ou None se não encontrado
    """
    pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        logger.warning("[extract_json] Padrão não encontrado no HTML.")
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        logger.error(f"[extract_json] Erro ao decodificar JSON: {e}")
        return None


def parse_video(data: dict) -> dict | None:
    """
    Extrai campos do vídeo a partir do JSON da página TikTok.

    Returns:
        dict com id, desc, author, likes, views, video_url
        ou None se estrutura inesperada
    """
    try:
        item = (
            data["__DEFAULT_SCOPE__"]
                ["webapp.video-detail"]
                ["itemInfo"]
                ["itemStruct"]
        )
        author_id = item["author"]["uniqueId"]
        video_id  = item["id"]

        return {
            "id":       video_id,
            "desc":     item.get("desc", ""),
            "author":   author_id,
            "likes":    item["stats"]["diggCount"],
            "views":    item["stats"]["playCount"],
            # URL pública canônica — não exige autenticação (CDN Akamai bloquearia)
            "video_url": f"https://www.tiktok.com/@{author_id}/video/{video_id}",
        }
    except KeyError as e:
        logger.error(f"[parse_video] Chave ausente no JSON: {e}")
        return None


def get_download_url(tiktok_url: str) -> dict:
    """
    Obtém links diretos de download via tikwm.com API.
    Não exige cookies ou autenticação TikTok.

    Args:
        tiktok_url: URL pública do vídeo (https://www.tiktok.com/@user/video/ID)

    Returns:
        dict com:
            url_sd  → vídeo sem marca d'água (SD)
            url_hd  → vídeo sem marca d'água (HD, se disponível)
            url_wm  → vídeo com marca d'água

    Raises:
        Exception: se a API falhar ou retornar erro
    """
    try:
        resp = requests.post(
            TIKWM_API,
            data={
                "url":    tiktok_url,
                "count":  12,
                "cursor": 0,
                "web":    1,
                "hd":     1,
            },
            headers={"User-Agent": Config.get_random_user_agent()},
            timeout=Config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("code") != 0:
            raise Exception(payload.get("msg", "Resposta inesperada da API tikwm"))

        d = payload["data"]

        def fix_url(path: str) -> str:
            """tikwm pode retornar caminho relativo — garante URL absoluta."""
            if not path:
                return ""
            if path.startswith("http"):
                return path
            return f"https://www.tikwm.com{path}"

        return {
            "url_sd": fix_url(d.get("play", "")),    # sem marca d'água (SD)
            "url_hd": fix_url(d.get("hdplay", "")),  # sem marca d'água (HD)
            "url_wm": fix_url(d.get("wmplay", "")),  # com marca d'água
        }

    except requests.RequestException as e:
        raise Exception(f"Erro na requisição à tikwm API: {e}") from e
    except (KeyError, ValueError) as e:
        raise Exception(f"Resposta inválida da tikwm API: {e}") from e
