from app.models.user import User
from app.errors import UserNotFound, DatabaseError
from app.constants import USER_ALLOWED_FIELDS
from app.constants import Resource, Status, Action
from app.services import audit_service
from app.logger import get_logger

logger = get_logger(__name__)

def create_user(claims):
    user = User(
        auth0_id = str(claims['sub']),
        name = str(claims['name']),
        email = str(claims['email']),
        picture =str(claims['picture'])
    )
    
    try:
        user.save()
    except Exception as e:
        logger.exception("create_user save failed auth0_id=%s error=%s", user.auth0_id, str(e))
        audit_service.log_event(
            actor_id=str(claims.get('sub')),
            resource_type=Resource.PROFILE,
            resource_id=None,
            event_type=Action.CREATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=None,
            after=None,
            idempotency_key=str(claims.get('sub')),
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.CREATE,
        status=Status.SUCCESS,
        error_message=None,
        before=None,
        after=user.to_dict(),
        idempotency_key=str(user.id),
    )
    return user

def sync_user(user, claims):
    before = user.to_dict()
    user.auth0_id = str(claims.get('sub', user.auth0_id))
    user.name = str(claims.get('name', user.name))
    user.email = str(claims.get('email', user.email))
    user.picture = str(claims.get('picture', user.picture))

    try:
        user.save()
    except Exception as e:
        logger.exception("sync_user save failed user_id=%s error=%s", user.id, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=str(user.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=before,
            after=None,
            idempotency_key=str(user.id),
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=before,
        after=user.to_dict(),
        idempotency_key=str(user.id),
    )
    return {'success': user}

def update_user(user, data):
    before = user.to_dict()
    for field in USER_ALLOWED_FIELDS:
        value = data.get(field, None)
        if value is not None:
            if field == 'venmo' and value == '':
                value = None
        setattr(user, field, value)
    try:
        user.save()
    except Exception as e:
        logger.exception("update_user save failed user_id=%s error=%s", user.id, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=str(user.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=before,
            after=None,
            idempotency_key=str(user.id),
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=before,
        after=user.to_dict(),
        idempotency_key=str(user.id),
    )
    return user

def get_user(uid):
    user = User.objects(id=uid).first()
    if not user:
        logger.warning("get_user not found user_id=%s", uid)
        raise UserNotFound(uid)
    return user

def get_users(ids):
    users = User.objects(id__in=ids).only('name', 'picture')
    return [
        {
            'name': user.name,
            'picture': user.picture
        }
        for user in users
    ]

def add_plan(plan, user):
    before = user.to_dict()
    if plan.organizer == user:
        user.hosting_count += 1
    else:
        user.participating_count += 1

    try:
        user.save()
    except Exception as e:
        logger.exception("add_plan save failed user_id=%s plan_id=%s error=%s", user.id, plan.id, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=str(user.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=before,
            after=None,
            idempotency_key=f"{user.id}:plan:{plan.id}:add",
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=before,
        after=user.to_dict(),
        idempotency_key=f"{user.id}:plan:{plan.id}:add",
    )
    return user

def add_mutuals(plan, user):
    try:
        everyone = set([p for p in plan.participants])
        everyone.add(plan.organizer)
        if user in everyone:
            everyone.remove(user)

        User.objects(id__in=[str(p.id) for p in everyone]).update(add_to_set__mutuals=user)
        User.objects(id=user.id).update(add_to_set__mutuals=everyone)

    except Exception as e:
        logger.exception("add_mutuals failed user_id=%s plan_id=%s error=%s", user.id, plan.id, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=str(user.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=None,
            after=None,
            idempotency_key=f"{user.id}:plan:{plan.id}:mutuals",
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=None,
        after={"plan_id": str(plan.id)},
        idempotency_key=f"{user.id}:plan:{plan.id}:mutuals",
    )
    return user

def remove_plan(plan, user):
    before = user.to_dict()
    if plan.organizer_id != user.id:
        user.participant_count -= 1
    else:
        user.hosting_count -= 1
    user.plans.remove(plan.id)

    try:
        user.save()
    except Exception as e:
        logger.exception("remove_plan save failed user_id=%s plan_id=%s error=%s", user.id, plan.id, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=str(user.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=before,
            after=None,
            idempotency_key=f"{user.id}:plan:{plan.id}:remove",
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(user.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=before,
        after=user.to_dict(),
        idempotency_key=f"{user.id}:plan:{plan.id}:remove",
    )
    return user
