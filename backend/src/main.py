import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, request
from flask_cors import CORS
from flask_migrate import Migrate  # type: ignore


env_path_root = Path(__file__).parent.parent.parent / ".env"
env_path_backend = Path(__file__).parent.parent / ".env"

logger = logging.getLogger(__name__)
if env_path_root.exists():
    load_dotenv(dotenv_path=env_path_root)
    logger.info("Carregando .env da raiz: %s", env_path_root)
elif env_path_backend.exists():
    load_dotenv(dotenv_path=env_path_backend)
    logger.info("Carregando .env do backend: %s", env_path_backend)
else:
    load_dotenv()

from src.config._env_guard import ensure_required_env
from src.models import db
from src.monitoring.logging_config import setup_logging
from src.monitoring.metrics import metrics_collector
from src.routes.admin import admin_bp
from src.routes.analytics import analytics_bp
from src.routes.appointments import bp as appointments_bp
from src.routes.assessments import bp as assessments_bp
from src.routes.audio_interview import bp as audio_interview_bp
from src.routes.auth import auth_bp
from src.routes.candidates import bp as candidates_bp
from src.routes.feedback import bp as feedback_bp
from src.routes.health import bp as health_bp
from src.routes.health_advanced import health_bp as health_advanced_bp
from src.routes.interviews import bp as interviews_bp
from src.routes.privacy import privacy_bp
from src.routes.product_intelligence import bp as product_intelligence_bp
from src.routes.reports import reports_bp
from src.routes.users import bp as users_bp
from src.routes.websocket import bp as websocket_bp
from src.security.middleware import setup_security_middleware
from src.services.websocket_service import init_socketio, setup_socketio_handlers
from src.utils.error_handler import register_error_handlers


def _sanitize_database_url(database_url):
    if database_url and database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _compose_database_url_from_parts():
    """Compõe DATABASE_URL a partir de POSTGRES_* quando possível.

    Evita que o backend quebre só porque DATABASE_URL não foi exportada
    explicitamente em ambientes que definem apenas POSTGRES_USER/PASSWORD/DB/HOST.
    Retorna None se as variáveis mínimas não estiverem presentes.
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")

    if not (user and password and db_name):
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def _database_config():
    is_testing = os.getenv("TESTING", "false").lower() == "true" or "pytest" in sys.modules

    if is_testing:
        database_url = "sqlite:///:memory:"
    else:
        database_url = os.getenv("DATABASE_URL") or _compose_database_url_from_parts()

        if not database_url:
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                raise RuntimeError(
                    "DATABASE_URL ausente e variáveis POSTGRES_USER/PASSWORD/DB "
                    "insuficientes para compor a URL em produção."
                )
            # Em dev, usa default do compose local.
            database_url = "postgresql://postgres:postgres@db:5432/postgres"

    database_url = _sanitize_database_url(database_url)
    engine_options = {}

    if not database_url.startswith("sqlite"):
        engine_options = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,
            "pool_reset_on_return": "commit",
            "connect_args": {
                "sslmode": "prefer",
                "connect_timeout": 10,
                "application_name": "apexus_hr_backend",
                "keepalives_idle": "600",
                "keepalives_interval": "30",
                "keepalives_count": "3",
            },
        }

    return database_url, engine_options


def create_app(include_socketio=False):
    ensure_required_env()

    app = Flask(__name__)
    database_url, engine_options = _database_config()
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32)),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", os.urandom(32)),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options,
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_SIZE", "50")) * 1024 * 1024,
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "/tmp/uploads"),
        SESSION_COOKIE_SECURE=os.getenv("ENVIRONMENT") == "production",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=3600,
        REDIS_URL=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        TESTING=os.getenv("TESTING", "false").lower() == "true",
        DEBUG=os.getenv("DEBUG", "false").lower() == "true",
        ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),
        CORS_ORIGINS=os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5000,https://localhost:5000,http://localhost:3000,"
            "https://localhost:3000,http://127.0.0.1:5000,https://127.0.0.1:5000",
        ),
    )

    app.url_map.strict_slashes = False

    origins = [origin.strip() for origin in app.config["CORS_ORIGINS"].split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins, "supports_credentials": True}})

    logger = setup_logging(app)
    logger.info("Starting application in %s mode", app.config["ENVIRONMENT"])

    db.init_app(app)
    Migrate(app, db)

    setup_security_middleware(app)
    register_error_handlers(app)

    @app.before_request
    def before_request():
        g.start_time = time.time()
        metrics_collector.active_connections += 1
        logger.info("Request started: %s %s", request.method, request.path)

    @app.after_request
    def after_request(response):
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            metrics_collector.record_request(
                request.method,
                request.endpoint or "unknown",
                response.status_code,
                duration,
            )
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            if hasattr(g, "request_id"):
                response.headers["X-Request-ID"] = g.request_id

        metrics_collector.active_connections = max(0, metrics_collector.active_connections - 1)
        return response

    app.register_blueprint(health_bp)
    app.register_blueprint(health_advanced_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(candidates_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(audio_interview_bp)
    app.register_blueprint(interviews_bp, url_prefix="/api/interviews")
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(websocket_bp)
    app.register_blueprint(product_intelligence_bp)

    socketio_instance = None
    if include_socketio:
        socketio_instance = init_socketio(app)
        setup_socketio_handlers(socketio_instance)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/api/info")
    def app_info():
        return {
            "name": "Apexus HR",
            "version": "1.0.0",
            "environment": app.config["ENVIRONMENT"],
            "status": "running",
        }

    logger.info("Application created successfully")
    if include_socketio:
        return app, socketio_instance
    return app


app, socketio = create_app(include_socketio=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    if socketio:
        socketio.run(app, host="0.0.0.0", port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
