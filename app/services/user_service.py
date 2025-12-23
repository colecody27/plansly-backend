from app.models.user import User

def create_user(claims):
    try:
        user = User(
            auth0_id = str(claims['sub']),
            name = str(claims['name']),
            email = str(claims['email']),
            picture =str(claims['picture'])
        )
        user.save()
    except Exception as e:
        return {'error': 'Error creating user'}
    return {'success': user}

def sync_user(user, claims):
    try:
        user.auth0_id = str(claims.get('sub', user.auth0_id))
        user.name = str(claims.get('name', user.name))
        user.email = str(claims.get('email', user.email))
        user.picture = str(claims.get('picture', user.picture))
        user.save()
    except Exception as e:
        return {'error': 'Error creating user'}
    return {'success': user}
