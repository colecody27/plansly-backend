import secrets
from app.models.invitation import Invitation
from app.services import plan_service, user_service
from datetime import timezone, datetime, timedelta
from app.errors import DatabaseError, InviteNotFound, NotPlanOrganizer, UserNotAuthorized
from app.utils import _naive_utc
from app.logger import get_logger

LINK_VALIDITY = timedelta(days=3)

logger = get_logger(__name__)


def create_invite(plan_id):
    creation = _naive_utc(datetime.now(timezone.utc))
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
        logger.exception("create_invite save failed plan_id=%s error=%s", plan_id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    logger.info("create_invite created plan_id=%s invite_id=%s", plan_id, invite.id)
    return invite

def get_invite(plan, user):
    if user != plan.organizer and user not in plan.participants:
        raise UserNotAuthorized
    
    invite = plan.invitation
    if not invite:
        raise InviteNotFound

    if not valid_invite(plan, invite.id):
        expire_invite(invite)
        invite = create_invite(plan.id)
        plan.invitation = invite 
        try:
            plan.save()
        except Exception as e:
            logger.exception("get_invite save failed plan_id=%s error=%s", plan.id, str(e))
            raise DatabaseError("Unexpected database error", details={"exception": str(e)})

    return invite

# TODO - Throw exceptions instead of False, must be caught where used
def valid_invite(plan, invite_id):
    if str(plan.invitation.id) != invite_id:
        return False
    
    invite = Invitation.objects(id=invite_id).first()
    if not invite:
        return False
    
    curr_time = _naive_utc(datetime.now(timezone.utc))
    expires_at = _naive_utc(invite.expires_at)
    if expires_at and curr_time > expires_at or invite.uses >= invite.max_uses:
        return False
    
    return True
    
def accept_invite(plan, user):
    if user in plan.participants or user == plan.organizer:
        logger.info("accept_invite skipped user_id=%s plan_id=%s", user.id, plan.id)
        return plan
    
    invite = Invitation.objects(id=str(plan.invitation.id)).first()
    if not invite:
        logger.warning("accept_invite invite not found plan_id=%s", plan.id)
        raise InviteNotFound
    invite.uses += 1

    user_service.add_mutuals(plan, user)
    plan_service.add_participant(plan, user)
    user_service.add_plan(plan, user)

    try:
        invite.save()
    except Exception as e:
        logger.exception("accept_invite save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    
    logger.info("accept_invite success plan_id=%s user_id=%s", plan.id, user.id)
    return plan

def expire_invite(invite):
    invite.status = 'expired'
    try:
        invite.save()
    except Exception as e:
        logger.exception("expire_invite save failed invite_id=%s error=%s", invite.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return {'success'}
