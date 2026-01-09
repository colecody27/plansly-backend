from app.services import invitation_service, user_service
from app.models.plan import Plan
from app.models.user import User
from app.models.message import Message
from app.models.activity import Activity
from app.errors import DatabaseError, PlanNotFound, UserNotAuthorized, ActivityNotFound, NotPlanOrganizer
from mongoengine.queryset.visitor import Q


def create_plan(data, user):
    plan = Plan(
        name=data.get('name'),
        description=data.get('description'),
        type=data.get('type'),
        organizer=data.get('organizer_id'),
        deadline=data.get('deadline'),
        start_day=data.get('start_day'),
        end_day=data.get('end_day'),
        country=data.get('country'),
        state=data.get('city'),
        city=data.get('state')
    )

    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    plan.invitation = invitation_service.create_invite(plan.id)

    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def get_plans(user):
    plans = Plan.objects(Q(organizer=user) | Q(participants=user))

    return plans

def get_plan(plan_id, user):
    plan = Plan.objects(id=plan_id).first() 
    if not plan:
        raise PlanNotFound
    if plan.organizer != user and user not in plan.participants:
        raise UserNotAuthorized(user.id)
    
    return plan

def serialize_plan(plan_dict):
    plan_dict['organizer'] = user_service.get_user(plan_dict['participants'])
    plan_dict['participants'] = user_service.get_users(plan_dict['participants'])
    return plan_dict

def lock_plan(plan, user):
    if user.id != plan.organizer_id:
        raise NotPlanOrganizer

    status = 'active' if plan.status == 'locked' else 'locked'
    plan.status = status
    
    try:    
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def update_plan():
    pass 

def delete_plan():
    pass

# TODO - Update plan costs (indiviudal and total)
def create_activity(plan, proposer, data):
    activity = Activity(
        name=data.get('name', None),
        description=data.get('description', None),
        link=data.get('link', None),
        cost=data.get('cost', 0.0),
        start_time=data.get('start_time', None),
        end_time=data.get('end_time', None),
        votes=[proposer.name]
    )
    plan.activities.append(activity)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return {'success': activity}

def update_activity():
    pass

def delete_activity():
    pass

def add_participant(plan, uid):
    plan.participant_ids.append(uid)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def remove_participant(plan, organizer_id, participant_id):
    if plan.organizer_id != organizer_id:
        raise NotPlanOrganizer
    if participant_id in plan.participant_ids:
        plan.participant_ids.remove(participant_id)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def vote_activity(plan, activity_id, user):
    activity = next(
        (a for a in plan.activities if a.id == activity_id),
        None)
    if not activity:
        raise ActivityNotFound
    
    if user.auth0_id in activity.votes:
        activity.votes.remove(user.auth0_id)
    else:
        activity.votes.append(user.auth0_id)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def send_message(plan, user, message):
    if plan.status != 'active':
        raise UserNotAuthorized
    
    message = Message(
        sender_id=user.id,
        text=message
    )
    plan.messages.append(message)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return message








