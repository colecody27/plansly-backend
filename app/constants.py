from datetime import datetime
import os

# TODO - Verify that costs are never negative 

USER_ALLOWED_FIELDS={
    'name': str,
    'venmo': str,
    'bio': str,
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
    'image_id': str
}

ACTIVITY_ALLOWED_FIELDS={
    'name': str,
    'description': str,
    'link': str,
    'cost': float,
    'is_cost_per_person': bool,
    'start_time': datetime,
    'end_time': datetime,
    'country': str,
    'city': str,
    'state': str
}

IMAGE_ALLOWED_FIELDS={
    'filename': str,
    'filetype': str,
    'filesize': float
}
