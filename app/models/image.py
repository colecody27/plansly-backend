from mongoengine import StringField, ReferenceField, IntField, Document, DateField
from datetime import datetime, timezone

class Image(Document):
    key = StringField(required = True, unique = True)
    filename = StringField()
    filesize = IntField()
    filetype = StringField()
    uploaded_by = ReferenceField("User")
    uploaded_at = DateField(default=datetime.now(timezone.utc))
    upload_status = StringField(options=['pending', 'uploaded'], default='pending')

    def to_dict(self):
        return {
            "id": str(self.id),
            "key": self.key,
            "filename": self.filename,
            "filesize": str(self.filesize),
            "filetype": self.filesize,
            "uploaded_by": {
                "id": str(getattr(self.uploaded_by, "id", None)),
                "name": getattr(self.uploaded_by, "name", None),
                "picture": getattr(self.uploaded_by, "picture", None)
            } if self.uploaded_by else None,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "upload_status": self.upload_status
        }
