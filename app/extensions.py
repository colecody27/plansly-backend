from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

oauth = OAuth()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")