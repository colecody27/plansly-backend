from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services import plan_service, user_service
from app.errors import AppError, Unauthorized, Forbidden
from app.extensions import socketio
from collections import defaultdict

MAX_MESSAGE_LENGTH = 2000
active_users = defaultdict(set)

@socketio.on("connect")
def on_connect():
    try:
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
    except Exception as e:
        print("Socket auth failed:", repr(e), flush=True)
        raise ConnectionRefusedError("unauthorized")

    # Store identity for later events (per-socket), get's cleaned up on disconnects
    session['user_id'] = user_id

@socketio.on("plan:join")
def join_plan(data):
    try:
        uid = session.get('user_id')
        plan_id = data.get('plan_id')
        if not uid or not plan_id:
            emit("auth:error", {"code": "unauthorized"})
            return
        user = user_service.get_user(uid)
        if not plan_service.is_member(plan_id, user):
            emit("error", {"code": "forbidden"})
            return

        room = f"plan:{plan_id}"
        join_room(room) 

        active_users[plan_id].add(uid)
        session['plan_id'] = plan_id
        emit('plan:users', {'msg': len(active_users[plan_id])}, room=room)
        emit('plan:announcement', {'msg': f'{user.name} has joined the chat! 🤙'}, room=room)

    except Exception as e:
        emit("error", {
            "event": "join_plan",
            "error": e.error_code,
            "message": e.message
        })

@socketio.on("plan:leave")
def leave_plan(data):
    try:
        uid = session.get('user_id')
        plan_id = session.get('plan_id')
        if not uid or not plan_id:
            emit("auth:error", {"code": "unauthorized"})
            return
        
        user = user_service.get_user(uid)
        room = f"plan:{plan_id}"
        leave_room(room)

        active_users[plan_id].remove(uid)
        if len(active_users[plan_id]) == 0:
            emit('plan:users', {'msg': 0}, room=room)
            del active_users[plan_id]
        else:
            emit('plan:users', {'msg': len(active_users[plan_id]) }, room=room)
        if session.get('plan_id'): 
            del session['plan_id']

        emit('plan:announcement', {'msg': f'{user.name} has left the chat! 👋'}, room=room)

    except Exception as e:
        emit("error", {
            "event": "leave_plan",
            "error": e.error_code,
            "message": e.message
        })

@socketio.on("disconnect")
def on_disconnect():
    user_id = session.get('user_id')
    plan_id = session.get('plan_id')

    if user_id and plan_id:
        del session['plan_id']
        del session['user_id']
        active_users[plan_id].remove(user_id)
        if len(active_users[plan_id]) == 0:
            del active_users[plan_id]

def broadcast_event(event_name, payload):
    emit(event_name, )

@socketio.on("plan:message:send")
def send_message(data):
    try:
        uid = session.get('user_id')
        if not uid:
            emit("error", {"code": "unauthorized"})
            return
        user = user_service.get_user(uid)

        plan_id = data.get('plan_id')
        plan = plan_service.get_plan(plan_id, user)
        
        room = f"plan:{plan_id}"
        msg = data.get('message')
        if not msg:
            emit("error", {"code": "Message required"})
            return
        if len(msg) > MAX_MESSAGE_LENGTH:
            emit("error", {"code": "Message length too long"})
            return

        message = plan_service.send_message(plan, user, msg)
        print(message.to_dict())
        emit("plan:message:new", message.to_dict(), room=room)
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
