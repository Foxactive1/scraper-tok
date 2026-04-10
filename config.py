"""
config.py — InNovaIdeia / TikTok Scraper Pro
Configurações centralizadas via variáveis de ambiente.

Correções aplicadas:
  - Movido para app/config.py (consistência de imports — ver scraper.py e tasks.py)
  - CELERY_TASK_ALWAYS_EAGER controlado por env var
"""

import os
import random


class Config:
    # Redis — broker e backend Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Database (PostgreSQL ou outro — não utilizado ainda)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Timeout para requisições HTTP ao TikTok (segundos)
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 15))

    # Lista de proxies (formato: "http://user:pass@host:port")
    # Deixe vazio para desabilitar proxies
    PROXIES: list[str] = []

    # Celery: True apenas para testes locais sem Redis
    CELERY_TASK_ALWAYS_EAGER: bool = (
        os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
    )

    # User-Agents para rotação e redução de detecção bot
    USER_AGENTS: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    @staticmethod
    def get_random_user_agent() -> str:
        """Retorna um User-Agent aleatório da lista configurada."""
        return random.choice(Config.USER_AGENTS)
