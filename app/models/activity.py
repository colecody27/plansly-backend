from mongoengine import EmbeddedDocument, StringField, FloatField, DateTimeField, ListField, ReferenceField
from app.services.user_service import get_users
import uuid

class Activity(EmbeddedDocument):
    activity_id = StringField(required=True, default=lambda: str(uuid.uuid4())) # Embedded docs don't automatically get UIDs in mongodb
    name = StringField(required=True)
    description = StringField()
    link = StringField()
    cost = FloatField(default=0.0)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField()
    proposer = ReferenceField("User", required=True)
    status = StringField(choices=["proposed", "accepted", "rejected"], default="proposed")
    votes = ListField(ReferenceField("User"))

    def to_dict(self):
        return {
            'id': self.activity_id,
            'name': self.name,
            'description': self.description,
            'link': self.link,
            'cost': self.cost,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'proposer': self.proposer.name,
            'status': self.status,
            "votes": [
                {
                    "name": getattr(v, "name", None),
                    "picture": getattr(v, "picture", None)
                } 
                for v in self.votes
            ],
        }