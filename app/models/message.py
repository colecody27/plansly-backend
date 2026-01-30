from mongoengine import EmbeddedDocument, StringField, DateTimeField, ReferenceField
from datetime import datetime, timezone

class Message(EmbeddedDocument):
    sender = ReferenceField('User', required=True) 
    text = StringField(required=True)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'sender_id': str(getattr(self.sender, 'id', None)), 
            'sender_name': getattr(self.sender, 'name', None), 
            'text': self.text,
            'date': self.timestamp.isoformat()
        }