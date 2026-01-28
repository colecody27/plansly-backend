from app.services import invitation_service, user_service
from app.models.plan import Plan
from app.models.user import User
from app.models.message import Message
from app.models.activity import Activity, ActivityCost
from app.errors import DatabaseError, PlanNotFound, UserNotAuthorized, ActivityNotFound, NotPlanOrganizer
from mongoengine.queryset.visitor import Q
import uuid
from app.constants import PLAN_ALLOWED_FIELDS, ACTIVITY_ALLOWED_FIELDS


def create_plan(data, user):
    plan = Plan(
        name=data.get('name'),
        description=data.get('description'),
        type=data.get('type'),
        organizer=user,
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
        print(str(e))
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

def get_plan(plan_id, user=None):
    plan = Plan.objects(id=plan_id).first() 
    if not plan:
        raise PlanNotFound(plan_id)
    if user:
        if plan.organizer != user and user not in plan.participants:
            raise UserNotAuthorized(user.id)
    
    return plan

def serialize_plan(plan_dict):
    plan_dict['organizer'] = user_service.get_user(plan_dict['participants'])
    plan_dict['participants'] = user_service.get_users(plan_dict['participants'])
    return plan_dict

def lock_plan(plan, user):
    if user != plan.organizer:
        raise NotPlanOrganizer

    plan.status = 'active' if plan.status == 'locked' else 'locked'
    
    try:    
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def update_plan(plan, user, data):
    if user != plan.organizer:
        raise NotPlanOrganizer
    
    for field in PLAN_ALLOWED_FIELDS.keys():
        if field in data:
            setattr(plan, field, data[field])

    try:    
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def delete_plan():
    pass

def create_activity(plan, proposer, data):
    if plan.status != 'active':
        raise UserNotAuthorized
    cost = data.get('cost', 0.0)
    activity = Activity(
        name=data.get('name', None),
        description=data.get('description', None),
        proposer=proposer,
        link=data.get('link', None),
        costs=ActivityCost(per_person=cost, total_cost=cost, is_per_person=data.get('cost_is_per_person')),
        start_time=data.get('start_time', None),
        end_time=data.get('end_time', None)
    )
    plan.activities.append(activity)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return activity

def update_activity(plan, user, activity, data):
    if user != plan.organizer:
        raise UserNotAuthorized
    
    for field in ACTIVITY_ALLOWED_FIELDS:
        if field in data:
            setattr(activity, field, data[field])

    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return activity

def get_activity(plan, activity_id):
    activity = next((a for a in plan.activities if a.activity_id == activity_id), None)
    if not activity:
        raise ActivityNotFound
    
    return activity
    

def delete_activity():
    pass

# TODO - Update lock activity to be agnostic to activity id since this may also be used by organizer
def lock_activity(plan, activity_id, user=None):
    if user and user != plan.organizer:
        raise NotPlanOrganizer
    
    activity = next((a for a in plan.activities if a.activity_id == activity_id), None)
    if not activity:
        raise ActivityNotFound
    
    # Update activity status and plan costs
    total_participants = len(plan.participants) + 1
    activity.status = 'confirmed'
    plan.costs.total += float(activity.costs.total_cost)
    plan.costs.per_person = float(plan.costs.total/total_participants)

    # Update status of remaining activities to rejected
    rejected_activities = [a for a in plan.activities 
                        if a.activity_id != activity_id
                        if a.status == 'proposed'
                        and is_overlapped(a, activity)]
    for act in rejected_activities:
        act.status = 'rejected'

    try:
        plan.save()
    except Exception as e:
        print(str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return activity

def add_participant(plan, user):
    plan.participants.append(user)
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
        (a for a in plan.activities if a.activity_id == activity_id),
        None)
    if not activity:
        raise ActivityNotFound
    
    # Update votes and costs
    conflicting_activity = next((a for a in plan.activities 
                           if a.activity_id != activity_id
                           if a.status == 'proposed'
                           and user in a.votes
                           and is_overlapped(a, activity)), None)
    if conflicting_activity:
        conflicting_activity.votes.remove(user)
        update_activity_costs(conflicting_activity)
    if user in activity.votes:
        activity.votes.remove(user)
    else:
        activity.votes.append(user)
    update_activity_costs(activity)
    plan.save()

    try:
        # Finalize activity if max votes are reached
        if len(activity.votes) == (len(plan.participants) + 1):
            lock_activity(plan, activity_id)
        else:
            plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return activity

def update_activity_costs(activity):
    is_per_person = activity.costs.is_per_person
    votes = len(activity.votes)
    
    # Update total cost
    if is_per_person:
        activity.costs.total_cost = activity.costs.per_person * len(activity.votes) if votes else activity.costs.per_person
    # Update per person cost
    else:
        activity.costs.per_person = float(activity.costs.total_cost/votes) if votes else activity.costs.total_cost
    

def is_overlapped(act_a, act_b):
    if act_a.start_time == act_b.start_time:
        return True
    # Actvity b start conflict
    if act_b.start_time < act_a.end_time and act_b.start_time > act_a.start_time:
        return True
    # Actvity a start conflict
    if act_a.start_time < act_b.end_time and act_a.start_time > act_b.start_time:
        return True
    
    return False

def send_message(plan, user, message):
    message = Message(
        sender=user,
        text=message
    )
    plan.messages.append(message)
    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return message

def pay(plan, user):
    if plan.status != 'locked':
        raise UserNotAuthorized
    
    for act in plan.activities:
        if user in act.votes and user not in act.payments:
            plan.costs.collected += act.costs.per_person
            act.payments.append(user)

    try:
        plan.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan


def is_member(plan_id, user_id):
    plan = Plan.objects(id=plan_id).first()
    if not plan:
        return False
    if user_id not in [str(p.id) for p in plan.participants] and user_id != str(plan.organizer.id):
        print(f'user_id: {user_id}')
        print(f'org_id: {str(plan.organizer.id)}')
        print('this is false')
        return False
    return True



