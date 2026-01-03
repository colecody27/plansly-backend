from app.models.user import User
from app.errors import UserNotFound, DatabaseError

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
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return {'success': user}

def get_user(uid):
    user = User.objects(id=uid).first()
    if not user:
        raise UserNotFound(uid)
    return user

def get_users(ids):
    return User.objects(auth0_id__in=ids).only('name')

def add_plan(plan, user):
    if plan.organizer_id != user.id:
        user.participant_count += 1
    else:
        user.hosting_count += 1
    user.plans.append(plan.id)

    try:
        user.save()
    except Exception as e:
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
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return user