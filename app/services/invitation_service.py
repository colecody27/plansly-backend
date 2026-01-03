import secrets
from app.models.invitation import Invitation
from app.services import plan_service, user_service
from datetime import timezone, datetime, timedelta
from app.errors import DatabaseError, InviteNotFound, NotPlanOrganizer

LINK_VALIDITY = timedelta(days=3)

def create_invite(plan_id):
    creation = datetime.now(timezone.utc)
    expiry = creation + LINK_VALIDITY
    link = secrets.token_urlsafe(32) # TODO - Verify that generated token is unique

    invite = Invitation(
        link=link,
        created_at=creation,
        expires_at=expiry, 
        plan_id=plan_id
    )
    try:
        invite.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return invite

def get_invite(plan, user):
    if user.id != plan.organizer_id:
        raise NotPlanOrganizer
    
    invite = Invitation.objects(plan.invitation_id).first()
    if not invite:
        raise InviteNotFound

    if not valid_invite(invite.id):
        expire_invite(invite)
        invite = create_invite(plan.id)
        plan.invitation_id = invite.id # TODO - Use update plan logic instead
        try:
            plan.save()
        except Exception as e:
            raise DatabaseError("Unexpected database error", details={"exception": str(e)})

    return invite

def valid_invite(invite_id):
    invite = Invitation.objects(invite_id).first()
    if not invite:
        return False
    
    curr_time = datetime.now(timezone.utc)
    if curr_time > invite.expires_at or invite.uses >= invite.max_uses:
        return False
    
    return True
    
def accept_invite(plan, user):
    plan_service.add_participant(plan, user)
    user_service.add_plan(plan, user)

    invite = Invitation.objects(id=plan.invitation_id).first()
    if not invite:
        raise InviteNotFound
    invite.uses += 1

    try:
        invite.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    
    return plan

def expire_invite(invite):
    invite.status = 'expired'
    try:
        invite.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return {'success'}


