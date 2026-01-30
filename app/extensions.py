from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import redis 
import os
import boto3

oauth = OAuth()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins=["http://127.0.0.1:5173"])
cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True,
)
aws_region = os.getenv("AWS_REGION_NAME")
s3 = boto3.client("s3", region_name=aws_region)
