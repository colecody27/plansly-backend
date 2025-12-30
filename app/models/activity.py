from mongoengine import EmbeddedDocument, StringField, FloatField, DateTimeField, ListField

class Activity(EmbeddedDocument):
    name = StringField(required=True)
    description = StringField()
    link = StringField()
    cost = FloatField(default=0.0)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField()
    proposer_id = StringField(required=True)
    status = StringField(choices=["proposed", "accepted", "rejected"], default="proposed")
    votes = ListField(StringField())

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'link': self.link,
            'cost': self.cost,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'proposer_id': self.proposer_id,
            'status': self.status,
            'votes': self.votes
        }