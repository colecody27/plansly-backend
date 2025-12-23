from mongoengine import Document, StringField, ListField, IntField, BooleanField, ReferenceField

class User(Document):
    # Account Metadata
    auth0_id = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    name = StringField()
    picture = StringField()
    provider = StringField()    
    linked_accounts = ListField(StringField())

    # Trip References
    plans = ListField(ReferenceField('Plan'))
    hosting_count = IntField(default=0)
    participating_count = IntField(default=0)

    # Preferences
    notifications = BooleanField()
    light_theme = BooleanField()
    currency = StringField()
