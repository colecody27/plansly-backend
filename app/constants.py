from datetime import datetime
import os
from enum import Enum

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
    'image_id': str,
    'image_key': str,
    'is_public': bool
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

AWS_S3_URL='https://plannit-s3-test-bucket.s3.us-west-1.amazonaws.com/stock'
S3_STOCK_IMAGE_URLS = {
    'abstract': [f'{AWS_S3_URL}/abstract/abstract{i}.jpg' for i in range(1, 8)],
    'adventure': [f"{AWS_S3_URL}/adventure/travel{i}.jpg" for i in range(1, 10)],
    'social': [f'{AWS_S3_URL}/social/social{i}.jpg' for i in range(1, 5)],
    'food': [f'{AWS_S3_URL}/food/dinner{n}.jpg' for n in range(1, 10)],
}

class Status(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'

class Resource(Enum):
    TRIP = 'trip'
    EVENT = 'event'
    GROUP_PURCHASE = 'group_purchase'
    ACTIVITY = 'activity'
    MESSAGE = 'message'
    INVITE = 'invite'
    PROFILE = 'profile'

class Action(Enum):
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'DELETE'

