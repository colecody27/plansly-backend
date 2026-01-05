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
    organizer_id = ReferenceField('User', required=True)  
    participant_ids = ListField(ReferenceField('User'))
    name = StringField()
    description = StringField()
    deadline = DateTimeField()
    costs = EmbeddedDocumentField(PlanCosts)
    activities = ListField(EmbeddedDocumentField('Activity'))
    messages = ListField(EmbeddedDocumentField('Message'))
    invitation_id = ReferenceField('Invitation') 
    created_at = DateTimeField(default=datetime.utcnow)
    theme = StringField()

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            # 'organizer_id': str(self.organizer_id.name) if self.organizer_id else None,
            # 'participant_ids': [str(pid.id) for pid in self.participant_ids],
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'costs': {
                'total': self.costs.total if self.costs else 0.0,
                'per_person': self.costs.per_person if self.costs else 0.0
            },
            'activities': [activity.to_dict() for activity in self.activities],
            'messages': [message.to_dict() for message in self.messages],
            'invitation_id': str(self.invitation_id) if self.invitation_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }