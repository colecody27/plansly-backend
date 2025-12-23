from mongoengine import Document, StringField, DateTimeField, FloatField, EmbeddedDocumentField, ListField, EmbeddedDocument, ReferenceField
from datetime import datetime

class PlanCosts(EmbeddedDocument):
    total = FloatField(default=0.0)
    per_person = FloatField(default=0.0)

class Plan(Document):
    type = StringField(
        choices=["trip", "event", "group_purchase"],
        required=True
    )
    status = StringField(default="active")
    organizer_id = ReferenceField('User', required=True)  
    participant_ids = ListField(ReferenceField(User))
    description = StringField()
    deadline = DateTimeField()
    costs = EmbeddedDocumentField(PlanCosts)
    activities = ListField(EmbeddedDocumentField('Activity'))
    messages = ListField(EmbeddedDocumentField('Message'))
    invitation_id = ReferenceField('Invitation') 
    created_at = DateTimeField(default=datetime.utcnow)