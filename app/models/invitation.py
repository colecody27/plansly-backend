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

    def to_dict(self):
        return {
            "id": str(self.id),
            "link": self.link,
            "plan_id": str(self.plan_id.id) if self.plan_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "uses": self.uses,
            "max_uses": self.max_uses
        }