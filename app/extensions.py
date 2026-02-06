from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import redis 
import os
import boto3
from botocore.config import Config


oauth = OAuth()
jwt = JWTManager()
socketio = SocketIO(
    cors_allowed_origins=[os.environ.get('FRONTEND_URL')],
    async_mode='eventlet'
    )
cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True,
)
aws_region = os.getenv("AWS_REGION_NAME")
s3 = boto3.client("s3", region_name=aws_region, config=Config(signature_version="s3v4"))
