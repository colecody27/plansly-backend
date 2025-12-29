from datetime import datetime

USER_ALLOWED_FIELDS={
    'name': str,
    'light_mode': bool,
    'notifications': bool,
    'currency': str
}

PLAN_ALLOWED_FIELDS={
    'name': str,
    'description': str,
    'deadline': datetime,
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