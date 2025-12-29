from mongoengine import Document, StringField, DateTimeField, IntField, ReferenceField
from datetime import datetime

class Invitation(Document):
    link = StringField(required=True)
    plan_id = ReferenceField("Plan", required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField(required=True)
    status = StringField(
        choices=["active", "expired", "used"],
        default="active"
    )
    uses = IntField(default=0)
    max_uses = IntField(default=50)