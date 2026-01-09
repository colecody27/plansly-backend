from datetime import datetime

USER_ALLOWED_FIELDS={
    'name': str,
    'picture': str,
    'notifications': bool,
    'light_theme': bool,
    'country': str, 
    'city': str, 
    'state': str
}

PLAN_ALLOWED_FIELDS={
    'name': str,
    'description': str,
    'deadline': datetime,
    'start_day': datetime,
    'end_day': datetime,
    'country': str,
    'city': str,
    'state': str,
    'theme': str,
    'type': str,
}

ACTIVITY_ALLOWED_FIELDS={
    'name': str,
    'description': str,
    'link': str,
    'cost': float,
    'start_time': datetime,
    'end_time': datetime,
    'deadline': datetime
}
