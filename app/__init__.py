
from flask import Flask, request, g
from dotenv import find_dotenv, load_dotenv
from os import environ as env
from psycopg_pool import ConnectionPool
from authlib.integrations.flask_client import OAuth
from flask_cors import CORS
import uuid

# Load .env as early as possible so extensions init can read env vars
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

from app.extensions import oauth, jwt, socketio
from app.services.auth import Auth0JWTBearerTokenValidator
from mongoengine import connect
from app.errors import AppError
from app.logger import init_app
from datetime import timedelta
# from app.logger import init_app
# from app.config import Config

def create_app():
    app = Flask(__name__)    
    is_prod = env.get('ENV') == 'production'
    app.config.update(
        JWT_TOKEN_LOCATION=["headers", "cookies"],
        JWT_COOKIE_SECURE=is_prod,
        JWT_COOKIE_SAMESITE="Lax",
        JWT_COOKIE_CSRF_PROTECT=True,
        JWT_COOKIE_DOMAIN=".plansly.co" if is_prod else None,
    )
    CORS(
        app,
        resources={r"/*": {"origins": [env.get('FRONTEND_URL')]}},
        supports_credentials=True,  
    )

    init_app(app)
    socketio.init_app(app)
    from app.sockets import socket

    # Connect blueprints 
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.plan import plan_bp
    app.register_blueprint(plan_bp)
    from app.routes.user import user_bp
    app.register_blueprint(user_bp)

    app.secret_key = env.get("AUTH0_SECRET_KEY")

    app.auth0_validator = Auth0JWTBearerTokenValidator(
        domain=env.get('AUTH0_DOMAIN'),
        audience=env.get('AUTH0_CLIENT_ID')
    )

    REQUEST_ID_HEADER = "X-Request-Id"
    @app.before_request
    def assign_request_id():
        # Prefer upstream-provided ID if present; otherwise generate one
        rid = request.headers.get(REQUEST_ID_HEADER)
        if not rid:
            rid = str(uuid.uuid4())

        g.request_id = rid

    @app.after_request
    def add_request_id_header(response):
        response.headers[REQUEST_ID_HEADER] = getattr(g, "request_id", "")
        return response

    @app.errorhandler(AppError)
    def handle_app_error(err):
        app.logger.warning(
            "app_error code=%s status=%s message=%s",
            err.error_code,
            err.status_code,
            err.message,
        )
        response = {
            "error": err.error_code,
            "message": err.message,
        }
        if err.details:
            response["details"] = err.details
        return response, err.status_code

    oauth.init_app(app)
    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
    )
    jwt.init_app(app)
    connect(
        host=env.get("MONGO_URI"),
        uuidRepresentation="standard"
    )

    def make_pg_dsn():
        host = env.get("PGHOST")
        port = env.get("PGPORT", "5432")
        db   = env.get("PGDATABASE")
        user = env.get("PGUSER")
        pw   = env.get("PGPASSWORD")
        ssl  = env.get("PGSSLMODE", "require")

        # Note: passwords with special chars should be URL-encoded if you use a URL DSN.
        return f"postgresql://{user}:{pw}@{host}:{port}/{db}?sslmode={ssl}"

    app.pg_pool = ConnectionPool(
        conninfo=make_pg_dsn(),
        min_size=1,
        max_size=3,
        timeout=10,          
    )

    return app
