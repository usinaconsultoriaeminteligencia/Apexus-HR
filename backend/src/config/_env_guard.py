"""Environment guard to ensure required variables are set in production.

This module provides a helper that should be called on application startup
to verify that critical secrets and connection strings are provided via
environment variables. If the application is running in a production
environment (as indicated by the ``ENVIRONMENT`` variable), any missing
secret will cause an exception to be raised. In non-production
environments the guard does nothing to simplify local development.
"""

import os


_SECRET_VARS = ("SECRET_KEY", "JWT_SECRET_KEY", "OPENAI_API_KEY")


def _has_database_config() -> bool:
    """Aceita DATABASE_URL OU o trio POSTGRES_USER/PASSWORD/DB."""
    if os.getenv("DATABASE_URL"):
        return True
    required_parts = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    return all(os.getenv(var) for var in required_parts)


def _has_redis_config() -> bool:
    """Aceita REDIS_URL OU REDIS_HOST."""
    return bool(os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"))


def ensure_required_env() -> None:
    """Aborta o boot se variáveis críticas estiverem ausentes em produção.

    Requisitos em produção:
      - SECRET_KEY: segredo de sessão Flask
      - JWT_SECRET_KEY: segredo para assinatura de JWT
      - OPENAI_API_KEY: chave da OpenAI (fallbacks locais são apenas para dev)
      - Conectividade de banco: DATABASE_URL OU POSTGRES_USER/PASSWORD/DB
      - Conectividade de cache: REDIS_URL OU REDIS_HOST

    Em dev/staging, a função retorna silenciosamente.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment != "production":
        return

    missing = [var for var in _SECRET_VARS if not os.getenv(var)]

    if not _has_database_config():
        missing.append("DATABASE_URL (ou POSTGRES_USER+POSTGRES_PASSWORD+POSTGRES_DB)")

    if not _has_redis_config():
        missing.append("REDIS_URL (ou REDIS_HOST)")

    if missing:
        raise RuntimeError(
            "Missing required environment variables in production: "
            + ", ".join(missing)
        )
