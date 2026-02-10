from mongoengine import Document, StringField, ListField, IntField, BooleanField, ReferenceField

class User(Document):
    # Account Metadata
    auth0_id = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    phone = StringField()
    venmo = StringField(unique=True, sparse=True, null=True) 
    name = StringField()
    picture = StringField()
    provider = StringField()    
    linked_accounts = ListField(StringField())
    preferred_comms = ListField(StringField())
    country = StringField()
    state = StringField()
    city = StringField()
    bio = StringField()
    mutuals = ListField(ReferenceField('User'))

    # Trip Metadata
    hosting_count = IntField(default=0)
    participating_count = IntField(default=0)

    # Preferences
    notifications = BooleanField() # TODO - Add notifications that are currently provided on frontend
    light_theme = BooleanField()

    def to_dict(self):
        return {
            "id": str(self.id),
            "venmo": self.venmo,
            "bio": self.bio,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "hosting_count": self.hosting_count,
            "participating_count": self.participating_count,
            "notifications": self.notifications,
            "light_theme": self.light_theme,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            "mutuals": [
                {
                    'id': str(m.id),
                    'name': m.name,
                    'picture': m.picture,
                }
                for m in self.mutuals
            ]
        }
