from mongoengine import EmbeddedDocument, StringField, DateTimeField
from datetime import datetime

class Message(EmbeddedDocument):
    sender_id = StringField(required=True) 
    text = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)