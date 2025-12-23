from mongoengine import EmbeddedDocument, StringField, FloatField, DateTimeField, ListField

class Activity(EmbeddedDocument):
    name = StringField(required=True)
    description = StringField()
    link = StringField()
    cost = FloatField(default=0.0)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)
    proposer_id = StringField(required=True)
    status = StringField(choices=["proposed", "accepted", "rejected"], default="proposed")
    votes = ListField(StringField())