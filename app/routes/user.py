from flask import Blueprint, request, jsonify, url_for, session, redirect, render_template, abort, current_app
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app.models.user import User
from app.extensions import oauth
from app.services import user_service
from datetime import timedelta
from app.errors import Unauthorized
from app.utils import normalize_args
from app.constants import USER_ALLOWED_FIELDS

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user():
    uid = get_jwt_identity()
    if not uid:
        return jsonify({'error': 'Invalid token'})    

    user = user_service.get_user(uid)
    data = request.get_json()
    data = normalize_args(USER_ALLOWED_FIELDS, data)

    user = user_service.update_user(user, data)
    print(user.to_dict())

    return jsonify({'success': True,
            'data': user.to_dict(),
            'msg': 'User retreived succesfully'}), 200



@user_bp.route('', methods=['GET'])
@jwt_required()
def get_user():
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized

    user = user_service.get_user(uid)

    return jsonify({'success': True,
                'data': user.to_dict(),
                'msg': 'User retreived succesfully'}), 200

@user_bp.route('', methods=['PUT'])
@jwt_required()
def add_mutuals():
    pass 
