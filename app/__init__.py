
from flask import Flask
from dotenv import find_dotenv, load_dotenv
from os import environ as env
from authlib.integrations.flask_client import OAuth
from app.extensions import oauth, jwt
from app.services.auth_service import Auth0JWTBearerTokenValidator
from mongoengine import connect
# from app.logger import init_app
# from app.config import Config

def create_app():
    app = Flask(__name__)
    # init_app(app) # Logging
    # app.config.from_object(Config) # Environment configurations
    # db.init_app(app) # Connect database 
    # jwt.init_app(app) # Connect JWT

    # Connect blueprints 
    from app.routes.auth_route import auth_bp
    app.register_blueprint(auth_bp)
    # from app.routes.alerts import alert_bp
    # app.register_blueprint(alert_bp)
    # from app.routes.sensors import sensor_bp
    # app.register_blueprint(sensor_bp)

    ENV_FILE = find_dotenv()
    if ENV_FILE:
        load_dotenv(ENV_FILE)

    app.secret_key = env.get("AUTH0_SECRET_KEY")

    app.auth0_validator = Auth0JWTBearerTokenValidator(
        domain=env.get('AUTH0_DOMAIN'),
        audience=env.get('AUTH0_CLIENT_ID')
    )

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