from mongoengine import Document, StringField, DateTimeField, FloatField, EmbeddedDocumentField, ListField, EmbeddedDocument, ReferenceField
from datetime import datetime
from app.models import activity, message

class PlanCosts(EmbeddedDocument):
    total = FloatField(default=0.0)
    per_person = FloatField(default=0.0)

class Plan(Document):
    type = StringField(
        choices=["trip", "event", "group_purchase"],
        required=True
    )
    status = StringField(
        default="active",
        options=['active', 'locked'])
    organizer = ReferenceField('User', required=True)  
    participants = ListField(ReferenceField('User'))
    name = StringField()
    description = StringField()
    deadline = DateTimeField()
    costs = EmbeddedDocumentField(PlanCosts)
    activities = ListField(EmbeddedDocumentField('Activity'))
    messages = ListField(EmbeddedDocumentField('Message'))
    invitation = ReferenceField('Invitation') 
    created_at = DateTimeField(default=datetime.utcnow)
    start_day = DateTimeField()
    end_day = DateTimeField()
    theme = StringField()
    country = StringField()
    state = StringField()
    city = StringField()
    
    meta = {
        "indexes": ["organizer"]
    }

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            "organizer": {
                'name': self.organizer.name,
                'picture': self.organizer.picture,
            },
            "participants": [
                {
                    'name': p.name,
                    'picture': p.picture,
                } 
                for p in self.participants
            ],
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'costs': {
                'total': self.costs.total if self.costs else 0.0,
                'per_person': self.costs.per_person if self.costs else 0.0
            },
            'activities': [activity.to_dict() for activity in self.activities],
            'messages': [message.to_dict() for message in self.messages],
            'invitation': str(self.invitation.id) if self.invitation else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'start_day': self.start_day.isoformat() if self.start_day else None,
            'end_day': self.end_day.isoformat() if self.end_day else None,
            'country': self.country,
            'state': self.state,
            'city': self.city
        }