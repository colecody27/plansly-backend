from flask import Blueprint, request, jsonify, url_for, session, redirect, render_template, abort, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app.models.user import User
from app.extensions import oauth
from app.services import user_service, plan_service
from datetime import timedelta
from app.constants import PLAN_ALLOWED_FIELDS
from app.utils import normalize_args

plan_bp = Blueprint('plan', __name__, url_prefix='/plan')

@plan_bp.route('/create', methods=['PUT'])
@jwt_required()
def create_plan():
    uid = get_jwt_identity()
    if not uid:
        return jsonify({'error': 'Invalid token'})    

    user = User.objects(auth0_id=uid).first()
    if not user:
        return jsonify({'error': 'User does not exist'})
    
    data = request.get_json()
    data['organizer_id'] = uid
    data = normalize_args(PLAN_ALLOWED_FIELDS, data)
    print(data)

    if 'error' in data:
        return jsonify({'error': 'Error reading plan data. Please try again.'})
    
    plan = plan_service.create_plan(data['success'])
    if 'error' in plan:
        return jsonify({'error': 'Error creating plan. Please try again.'})

    return jsonify({'success': plan.to_dict()})

@plan_bp.route('/<plan_id>', methods=['GET'])
@jwt_required()
def get_plan():
    pass

@plan_bp.route('', methods=['GET'])
@jwt_required()
def get_plans():
    pass

@plan_bp.route('/update/<plan_id>', methods=['POST'])
@jwt_required()
def update_plan():
    pass

@plan_bp.route('/delete/<plan_id>', methods=['DELETE'])
@jwt_required()
def delete_plan():
    pass

@plan_bp.route('/<plan_id>/activity/create', methods=['PUT'])
@jwt_required()
def create_activity():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['POST'])
@jwt_required()
def update_activity():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['GET'])
@jwt_required()
def get_activity():
    pass

@plan_bp.route('/<plan_id>/activity', methods=['GET'])
@jwt_required()
def get_activies():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['DELETE'])
@jwt_required()
def delete_activity():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>/vote', methods=['POST'])
@jwt_required()
def vote_activity():
    pass

@plan_bp.route('/<plan_id>', methods=['POST'])
@jwt_required()
def invite():
    pass

@plan_bp.route('/<plan_id>', methods=['POST'])
@jwt_required()
def add_participant():
    pass

@plan_bp.route('/<plan_id>', methods=['POST'])
@jwt_required()
def remove_participant():
    pass

@plan_bp.route('/<plan_id>', methods=['POST'])
@jwt_required()
def lock_plan():
    pass

@plan_bp.route('/<plan_id>', methods=['POST'])
@jwt_required()
def send_message():
    pass