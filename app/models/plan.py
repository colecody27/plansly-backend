from mongoengine import Document, StringField, DateTimeField, FloatField, EmbeddedDocumentField, ListField, EmbeddedDocument, ReferenceField, BooleanField
from datetime import datetime
from app.models import activity, message

class PlanCosts(EmbeddedDocument):
    total = FloatField(default=0.0)
    per_person = FloatField(default=0.0)
    collected = FloatField(default=0.0)

class Plan(Document):
    type = StringField(
        choices=["trip", "event", "group_purchase"],
        required=True
    )
    status = StringField(
        default="active",
        options=['active', 'locked', 'confirmed'])
    is_public = BooleanField(required=True, default=False)
    admins = ListField(ReferenceField('User'))
    organizer = ReferenceField('User', required=True)  
    participants = ListField(ReferenceField('User'))
    name = StringField()
    description = StringField()
    deadline = DateTimeField()
    costs = EmbeddedDocumentField(PlanCosts, default=PlanCosts)
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
    uploaded_images = ListField(ReferenceField('Image'))
    image = ReferenceField('Image')
    stock_image = StringField()
    
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
            'is_public': self.is_public,
            "organizer": {
                'id': str(self.organizer.id),
                'venmo': self.organizer.venmo,
                'name': self.organizer.name,
                'picture': self.organizer.picture,
            },
            "participants": [
                {
                    'id': str(p.id),
                    'name': p.name,
                    'picture': p.picture,
                } 
                for p in self.participants
            ],
            "admins": [
                {
                    'id': str(a.id),
                    'name': a.name,
                    'picture': a.picture,
                } 
                for a in self.admins
            ],
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'costs': {
                'total': self.costs.total if self.costs else 0.0,
                'per_person': self.costs.per_person if self.costs else 0.0,
                'collected': self.costs.collected
            },
            'activities': [activity.to_dict() for activity in self.activities],
            'messages': [message.to_dict() for message in self.messages],
            'invitation': str(self.invitation.id) if self.invitation else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'start_day': self.start_day.isoformat() if self.start_day else None,
            'end_day': self.end_day.isoformat() if self.end_day else None,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'images': {
                'primary': {
                    'id': str(getattr(self.image, 'id', None)),
                    'key': getattr(self.image, 'key', None)    
                },
                'stock': self.stock_image
            }
        }