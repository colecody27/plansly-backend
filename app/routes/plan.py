from flask import Blueprint, request, jsonify, url_for, session, redirect, render_template, abort, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app.models.user import User
from app.models.plan import Plan
from app.models.invitation import Invitation
from app.extensions import oauth
from app.services import user_service, plan_service, invitation_service, image_service
from datetime import timedelta
from app.constants import PLAN_ALLOWED_FIELDS, ACTIVITY_ALLOWED_FIELDS, IMAGE_ALLOWED_FIELDS, S3_STOCK_IMAGE_URLS, AWS_S3_URL
from app.utils import normalize_args
from app.errors import Unauthorized, InviteNotFound, InviteExpired

plan_bp = Blueprint('plan', __name__, url_prefix='/plan')

@plan_bp.route('/create', methods=['POST', 'PUT'])
@jwt_required()
def create_plan():
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized

    user = user_service.get_user(uid)

    data = request.get_json()
    print(data)
    normalize_args(PLAN_ALLOWED_FIELDS, data)
    print(data)

    plan = plan_service.create_plan(data, user)

    return jsonify({'success': True,
                    'data': plan.to_dict(),
                    'msg': 'Plan created succesfully'}), 200

@plan_bp.route('/<plan_id>', methods=['GET'])
@jwt_required()
def get_plan(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    if plan.image:
        selected_url = image_service.get_download_url(str(plan.image.key))
        uploaded_urls = image_service.get_download_urls(str(plan.image.key)) # TODO - Implement
    else:
        selected_url = f'{AWS_S3_URL}/{plan.stock_image}'
        uploaded_urls = []

    return jsonify({'success': True,
                    'data': {
                        'plan': plan.to_dict(),   
                        'image_urls': {
                            'selected': selected_url,
                            'uploaded': uploaded_urls
                        }
                    },
                    'msg': 'Plan retreived succesfully'}), 200

@plan_bp.route('', methods=['GET'])
@jwt_required()
def get_plans():
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plans = plan_service.get_plans(user)
    plans = [plan.to_dict() for plan in plans]
    
    for plan in plans:
        if plan.get('images').get('stock'):
            download_url = f"{AWS_S3_URL}/{plan['images']['stock']}"
        else:
            download_url = image_service.get_download_url(plan['images']['primary']['key'])
        plan['image_url'] = download_url

    return jsonify({'success': True,
                'data': plans,
                'msg': 'Plans retreived succesfully'}), 200

@plan_bp.route('/<plan_id>/update', methods=['PUT'])
@jwt_required()
def update_plan(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)

    data = request.get_json()
    normalize_args(PLAN_ALLOWED_FIELDS, data)
    print(data)

    plan = plan_service.update_plan(plan, user, data)

    return jsonify({'success': True,
                    'data': plan.to_dict(),
                    'msg': 'Plan created succesfully'}), 200

@plan_bp.route('/delete/<plan_id>', methods=['DELETE'])
@jwt_required()
def delete_plan():
    pass

@plan_bp.route('/<plan_id>/activity', methods=['POST'])
@jwt_required()
def create_activity(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    
    print(request.mimetype)     # should be application/json
    print(request.data)         # raw body
    print(request.is_json)      # True if JSON

    data = request.get_json()
    print('here')
    normalize_args(ACTIVITY_ALLOWED_FIELDS, data)
    print(data)
    
    plan = plan_service.get_plan(plan_id, user)
    activity = plan_service.create_activity(plan, user, data)
    
    return jsonify({'success': True,
            'data': activity.to_dict(),
            'msg': 'Activity created succesfully'}), 200

@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['PUT'])
@jwt_required()
def update_activity(plan_id, activity_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    data = request.get_json()
    normalize_args(ACTIVITY_ALLOWED_FIELDS, data)
    activity = plan_service.get_activity(plan, activity_id)
    activity = plan_service.update_activity(plan, user, activity, data)
    
    return jsonify({'success': True,
        'data': activity.to_dict(),
        'msg': 'Activity created succesfully'}), 200

# Activities are embedded in plans so shouldn't be needed
@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['GET'])
@jwt_required()
def get_activity():
    pass 

# Activities are embedded in plans so shouldn't be needed
@plan_bp.route('/<plan_id>/activity', methods=['GET'])
@jwt_required()
def get_activies():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>', methods=['DELETE'])
@jwt_required()
def delete_activity():
    pass

@plan_bp.route('/<plan_id>/activity/<activity_id>/vote', methods=['POST', 'PUT'])
@jwt_required()
def vote_activity(plan_id, activity_id):
    print('before uid')
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    print('after user')
    plan = plan_service.get_plan(plan_id, user)
    print('after plan')

    activity = plan_service.vote_activity(plan, activity_id, user)
    print('after activity')
    print(activity.to_dict())
    return jsonify({'success': True,
            'data': plan.to_dict(),
            'msg': 'Activity has been voted for succesfully'}), 200

@plan_bp.route('/<plan_id>/activity/<activity_id>/finalize', methods=['PUT'])
@jwt_required()
def lock_activity(plan_id, activity_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    
    activity = plan_service.lock_activity(plan, activity_id, user)
    
    return jsonify({'success': True,
            'data': activity.to_dict(),
            'msg': 'Activity has been voted for succesfully'}), 200

# TODO - Update invitations to use the generated link, must verify uniqueness when generating
@plan_bp.route('/<plan_id>/invite', methods=['GET'])
@jwt_required()
def get_invite(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    invite = invitation_service.get_invite(plan, user)
    
    invite = invite.to_dict()
    return jsonify({'success': True,
        'data': invite,
        'msg': 'Invite has been retreived succesfully'}), 200

@plan_bp.route('/<plan_id>/invite/<invite_id>', methods=['GET'])
def verify_invite(plan_id, invite_id):
    plan = plan_service.get_plan(plan_id)
    is_valid = invitation_service.valid_invite(plan, invite_id)
    if not is_valid:
        raise InviteExpired
    
    if plan.image:
        selected_url = image_service.get_download_url(str(plan.image.key))
        uploaded_urls = image_service.get_download_urls(str(plan.image.key)) # TODO - Implement
    else:
        selected_url = f'{AWS_S3_URL}/{plan.stock_image}'
        uploaded_urls = []
    return jsonify({'success': True,
                'data': {
                    'plan': plan.to_dict(),   
                    'image_urls': {
                        'selected': selected_url,
                        'uploaded': uploaded_urls
                    }
                },
                'msg': 'Invitation retreived succesfully'}), 200

@plan_bp.route('/<plan_id>/invite/<invite_id>/accept', methods=['POST'])
@jwt_required()
def accept_invite(plan_id, invite_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id)
    
    is_valid = invitation_service.valid_invite(plan, invite_id)
    if not is_valid:
        raise InviteExpired
    
    invitation_service.accept_invite(plan, user)
    return jsonify({'success': True,
        'data': plan.to_dict(),
        'msg': 'Invite accepted succesfully'}), 200

@plan_bp.route('/<plan_id>/participant/<participant_id>', methods=['DELETE'])
@jwt_required()
def remove_participant(plan_id, participant_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user.id)

    plan_service.remove_participant(plan, user, participant_id)
    user_service.remove_plan(plan, user)
    
    return jsonify({'success': True,
        'data': plan,
        'msg': 'Participant removed succesfully'}), 204

@plan_bp.route('/<plan_id>/lock-toggle', methods=['PUT'])
@jwt_required()
def lock_plan(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    plan_service.lock_plan(plan, user)

    return jsonify({'success': True,
        'data': plan.to_dict(),
        'msg': 'Plan locked succesfully'}), 204

@plan_bp.route('/<plan_id>/pay', methods=['PUT'])
@jwt_required()
def pay(plan_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
    plan = plan_service.get_plan(plan_id, user)
    plan = plan_service.pay(plan, user)

    return jsonify({'success': True,
        'data': plan.to_dict(),
        'msg': 'Plan locked succesfully'}), 204


@plan_bp.route('/upload/image', methods=['POST', 'PUT'])
@jwt_required()
def upload_image():
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)

    data = request.get_json()
    normalize_args(IMAGE_ALLOWED_FIELDS, data)
    pre_signed_url, image = image_service.get_upload_url(user, data)

    return jsonify({'success': True,
        'data': {
            'upload_url': pre_signed_url,
            'image_id': str(image.id)
        },
        'msg': 'Pre-signed URL generated succesfully'}), 200

@plan_bp.route('/upload/image/<image_id>', methods=['POST', 'PUT'])
@jwt_required()
def image_uploaded(image_id):
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    data = request.get_json()
    plan_id = data.get('plan_id')
    if plan_id:
        plan = plan_service.get_plan(plan_id)

    user = user_service.get_user(uid)
    image = image_service.get_image(image_id)
    image_service.image_uploaded(image)
    if plan:
        plan_service.update_image(plan, image)

    return jsonify({'success': True,
        'data': '',
        'msg': 'Image state updated succesfully'}), 204

@plan_bp.route('/stock/images', methods=['GET'])
@jwt_required()
def get_stock_images():
    uid = get_jwt_identity()
    if not uid:
        raise Unauthorized 

    user = user_service.get_user(uid)
   
    return jsonify({'success': True,
        'data': S3_STOCK_IMAGE_URLS,
        'msg': 'Stock image urls retreived successfully'}), 200