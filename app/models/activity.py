from mongoengine import EmbeddedDocument, EmbeddedDocumentField, StringField, FloatField, DateTimeField, ListField, ReferenceField, BooleanField
from app.services.user_service import get_users
import uuid

class ActivityCost(EmbeddedDocument):
    is_per_person = BooleanField(default=False)
    per_person = FloatField(default=0.0)
    total_cost = FloatField(default=0.0)

class Activity(EmbeddedDocument):
    activity_id = StringField(required=True, default=lambda: str(uuid.uuid4())) # Embedded docs don't automatically get UIDs in mongodb
    name = StringField(required=True)
    description = StringField()
    link = StringField()
    costs = EmbeddedDocumentField(ActivityCost, default=ActivityCost)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField()
    proposer = ReferenceField("User", required=True)
    status = StringField(choices=["proposed", "confirmed", "rejected"], default="proposed")
    votes = ListField(ReferenceField("User"))
    country = StringField()
    state = StringField()
    city = StringField()

    def to_dict(self):
        return {
            'id': self.activity_id,
            'name': self.name,
            'description': self.description,
            'link': self.link,
            'cost': {
                'per_person': self.costs.per_person,
                'is_per_person': self.costs.is_per_person,
                'total_cost': self.costs.total_cost
            },
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'proposer': {
                'id':  str(self.proposer.id),
                'name': self.proposer.name
            },
            'status': self.status,
            "votes": [
                {
                    "id": str(getattr(v, "id", None)),
                    "name": getattr(v, "name", None),
                    "picture": getattr(v, "picture", None)
                } 
                for v in self.votes
            ],
            'country': self.country,
            'state': self.state,
            'city': self.city
        }