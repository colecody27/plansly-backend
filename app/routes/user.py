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

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_prefernces():
    uid = get_jwt_identity()
    if not uid:
        return jsonify({'error': 'Invalid token'})    

    user = User(auth0_id=uid).first()
    if not user:
        return jsonify({'error': 'User does not exist'})
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    allowed_fields = {
        'name': str,
        'light_mode': bool,
        'notifications': bool,
        'currency': str
    }

    updated = False
    for field, field_type in allowed_fields.items():
        if field in data:
            value = data[field]
            try:
                if field_type == bool:
                    value = bool(value)
                elif field_type == str:
                    value = str(value).strip()
            except Exception as e:
                return jsonify({'error': f'Invalid type for {field}'}), 400

            if value == getattr(user, field, None):
                continue
            
            setattr(user, field, value)
            updated = True

    if updated:
        try:
            user.save()
        except Exception as e:
            return jsonify({'error': 'Error saving profile settings'})
        return jsonify({'message': 'Settings updated successfully'})
    return jsonify({'message': 'No valid fields provided'}), 400

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
