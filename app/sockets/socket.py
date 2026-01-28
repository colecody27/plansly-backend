from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services import plan_service, user_service
from app.errors import AppError, Unauthorized, Forbidden
from app.extensions import socketio

MAX_MESSAGE_LENGTH = 2000

@socketio.on("connect")
def on_connect():
    try:
        # token = request.cookies.get("plannit-token")
        # if not token:
        #     return False
        # decoded = decode_token(token)
        # user_id = decoded["sub"]

        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
        print(f'user_id: {user_id}')
    except Exception as e:
        print("Socket auth failed:", repr(e), flush=True)
        raise ConnectionRefusedError("unauthorized")

    # Store identity for later events (per-socket), get's cleaned up on disconnects
    session['user_id'] = user_id
    # join_room(f"plan:{plan_id}")

@socketio.on("join_plan")
def join_plan(data):
    try:
        print('here!')
        uid = session.get('user_id')
        plan_id = data.get('plan_id')
        is_member = plan_service.is_member(plan_id, uid)
        if not is_member:
            emit("error", {"code": "forbidden"})
            return

        room = f"plan:{plan_id}"
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
        plan_id = data.get(plan_id)
        room = f"plan:{plan_id}"
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
        uid = session.get('user_id')
        if not uid:
            emit("error", {"code": "unauthorized"})
            return
        user = user_service.get_user(uid)
        print('HERE')

        plan_id = data.get('plan_id')
        plan = plan_service.get_plan(plan_id, user)
        
        room = f"plan:{plan_id}"
        msg = data.get('message')
        if not msg:
            emit("error", {"code": "Message required"})
            return
        if len(msg) > MAX_MESSAGE_LENGTH:
            print(len(msg))
            emit("error", {"code": "Message length too long"})
            return

        message = plan_service.send_message(plan, user, msg)
        emit("new_message", message.to_dict(), room=room)
    except AppError as e:
        emit("error", {
            "event": "send_message",
            "error": e.error_code,
            "message": e.message
        })
    except Exception as e:
        print("send_message failed:", repr(e))
        emit("error", {
            "event": "send_message",
            "error": "server_error",
            "message": "Unexpected server error"
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

def current_user_id():
    _id = socketio.server.environ.get(request.sid).get("user_id")
    print(f"current user request_id: {request.sid}")
    print(f"id: {_id}")
    return _id
