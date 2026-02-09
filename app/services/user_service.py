from app.models.user import User
from app.errors import UserNotFound, DatabaseError
from app.constants import USER_ALLOWED_FIELDS
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
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return user

def sync_user(user, claims):
    user.auth0_id = str(claims.get('sub', user.auth0_id))
    user.name = str(claims.get('name', user.name))
    user.email = str(claims.get('email', user.email))
    user.picture = str(claims.get('picture', user.picture))

    try:
        user.save()
    except Exception as e:
        logger.exception("sync_user save failed user_id=%s error=%s", user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return {'success': user}

def update_user(user, data):
    for field in USER_ALLOWED_FIELDS:
        if data.get(field, None) is not None:
            setattr(user, field, data[field])
    try:
        user.save()
    except Exception as e:
        logger.exception("update_user save failed user_id=%s error=%s", user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
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
    if plan.organizer == user:
        user.hosting_count += 1
    else:
        user.participating_count += 1

    try:
        user.save()
    except Exception as e:
        logger.exception("add_plan save failed user_id=%s plan_id=%s error=%s", user.id, plan.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
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
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return user

def remove_plan(plan, user):
    if plan.organizer_id != user.id:
        user.participant_count -= 1
    else:
        user.hosting_count -= 1
    user.plans.remove(plan.id)

    try:
        user.save()
    except Exception as e:
        logger.exception("remove_plan save failed user_id=%s plan_id=%s error=%s", user.id, plan.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return user
