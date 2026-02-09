from flask import Blueprint, request, jsonify, url_for, session, redirect, render_template, abort, current_app
from flask_jwt_extended import create_access_token, set_access_cookies, unset_access_cookies
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app.models.user import User
from app.extensions import oauth, cache
from app.services import user_service
from app.errors import ValidationError
from datetime import timedelta
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route("/login")
def login():
    redirect_to = request.args.get('redirect_to')
    if redirect_to:
        session['redirect_to'] = redirect_to
    return oauth.auth0.authorize_redirect(
        redirect_uri=f"{env.get('BACKEND_URL')}/auth/callback"
    )

@auth_bp.route("/callback", methods=["GET", "POST"])
def callback():
    redirect_to = session.pop('redirect_to', f'{env.get('FRONTEND_URL')}/dashboard')
    token = oauth.auth0.authorize_access_token()
    id_token = token.get("id_token")
    if not id_token:
        abort(401, "No ID token returned from Auth0")

    # Validate auth0 token
    try:
        claims = current_app.auth0_validator.validate_token(id_token)
    except Exception as e:
        abort(401, f"Invalid Auth0 token: {str(e)}")
    
    # Create or sync user
    user = User.objects(auth0_id=claims['sub']).first()
    if user:
        user_service.sync_user(user, claims)
    else:
        user = user_service.create_user(claims)

    app_token = create_access_token(identity=str(user.id), expires_delta=timedelta(minutes=60))
    resp = redirect(redirect_to)

    set_access_cookies(resp, app_token)

    return resp

@auth_bp.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@auth_bp.route("/logout", methods=['GET'])
def logout():
    resp = redirect(env.get('FRONTEND_URL'))
    unset_access_cookies(resp)

    return resp
