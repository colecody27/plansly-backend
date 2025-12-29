import secrets
from app.models.invitation import Invitation
from datetime import timezone, datetime, timedelta

LINK_VALIDITY = timedelta(days=3)

def create_invite(plan_id):
    creation = datetime.now(timezone.utc)
    expiry = creation + LINK_VALIDITY
    link = secrets.token_urlsafe(32) # TODO - Verify that generated token is unique

    try:
        invite = Invitation(
            link=link,
            created_at=creation,
            expires_at=expiry, 
            plan_id=plan_id
        )
        invite.save()
    except Exception as e:
        return {'error': 'Error Creating invitation'}
    return invite

