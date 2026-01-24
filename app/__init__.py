
from flask import Flask
from dotenv import find_dotenv, load_dotenv
from os import environ as env
from authlib.integrations.flask_client import OAuth
from app.extensions import oauth, jwt, socketio
from app.services.auth import Auth0JWTBearerTokenValidator
from mongoengine import connect
from app.errors import AppError
from app.sockets.socket import socketio
from datetime import timedelta
# from app.logger import init_app
# from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=3)
    # init_app(app) # Logging
    # app.config.from_object(Config) # Environment configurations
    # db.init_app(app) # Connect database 
    # jwt.init_app(app) # Connect JWT
    socketio.init_app(app)
    from app.sockets import socket

    # Connect blueprints 
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.plan import plan_bp
    app.register_blueprint(plan_bp)
    from app.routes.user import user_bp
    app.register_blueprint(user_bp)

    ENV_FILE = find_dotenv()
    if ENV_FILE:
        load_dotenv(ENV_FILE)

    app.secret_key = env.get("AUTH0_SECRET_KEY")

    app.auth0_validator = Auth0JWTBearerTokenValidator(
        domain=env.get('AUTH0_DOMAIN'),
        audience=env.get('AUTH0_CLIENT_ID')
    )

    @app.errorhandler(AppError)
    def handle_app_error(err):
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

    return app