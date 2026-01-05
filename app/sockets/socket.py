from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token, jwt_required, get_jwt_identity
from app.services import plan_service, user_service
from app.errors import AppError, Unauthorized, Forbidden
from app.extensions import socketio

# TODO - Except specific exceptions

@socketio.on("connect")
@jwt_required()
def handle_connect():
    try:
        uid = get_jwt_identity()
    except Exception as e:
        emit("error", {
            "event": "connect",
            "error": e.error_code,
            "message": e.message
        })
        disconnect()

@socketio.on("join_plan")
def join_plan(data):
    try:
        uid = get_jwt_identity()
        user = user_service.get_user(uid)
        plan = plan_service.get_plan(data.get('plan_id'), user.id)
        room = f"plan:{plan.id}"
        join_room(room)
    except Exception as e:
        emit("error", {
            "event": "join_plan",
            "error": e.error_code,
            "message": e.message
        })

@socketio.on("leave_plan")
def leave_plan(data):
    try:
        uid = get_jwt_identity()
        user = user_service.get_user(uid)
        plan = plan_service.get_plan(data.get('plan_id'), user.id)
        room = f"plan:{plan.id}"
        leave_room(room)
    except Exception as e:
        emit("error", {
            "event": "leave_plan",
            "error": e.error_code,
            "message": e.message
        })

@socketio.on("send_message")
def send_message(data):
    try:
        uid = get_jwt_identity()
        user = user_service.get_user(uid)
        plan = plan_service.get_plan(data.get('plan_id'), user.id)
        room = f"plan:{plan.id}"
        message = plan_service.send_message(plan, user, data.get('message'))
        emit("new_message", message.to_dict(), room)
    except Exception as e:
        emit("error", {
            "event": "send_message",
            "error": e.error_code,
            "message": e.message
        })

@socketio.on_error_default
def socket_error_handler(e):
    if isinstance(e, AppError):
        emit("error", {
            "error": e.error_code,
            "message": e.message,
            "details": getattr(e, "details", None)
        })
    else:
        emit("error", {
            "error": "server_error",
            "message": "Unexpected server error"
        })
