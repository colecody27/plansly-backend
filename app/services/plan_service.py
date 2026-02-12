from app.services import invitation_service, user_service, image_service
from app.models.plan import Plan
from app.models.user import User
from app.models.message import Message
from app.models.activity import Activity, ActivityCost
from app.errors import DatabaseError, PlanNotFound, UserNotAuthorized, ActivityNotFound, NotPlanOrganizer, ValidationError, UserNotFound
from mongoengine.queryset.visitor import Q
import uuid
from app.constants import PLAN_ALLOWED_FIELDS, ACTIVITY_ALLOWED_FIELDS
from app.extensions import s3
import os
from datetime import datetime, timezone
from app.logger import get_logger

logger = get_logger(__name__)

def create_plan(data, user):
    image_id = data.get('image_id')
    logger.info("create_plan user_id=%s image_id=%s", user.id, image_id)

    plan = Plan(
        name=data.get('name'),
        description=data.get('description'),
        type=data.get('type'),
        organizer=user,
        is_public=data.get('is_public', False),
        deadline=data.get('deadline'),
        start_day=data.get('start_day'),
        end_day=data.get('end_day'),
        country=data.get('country'),
        state=data.get('city'),
        city=data.get('state'), 
        image=image_service.get_image(image_id) if image_id else None,
        stock_image=data.get('image_key'),
        uploaded_images=[image_id] if image_id else []
    )
    user.hosting_count += 1

    try:
        plan.save()
        user.save()
    except Exception as e:
        logger.exception("create_plan initial save failed user_id=%s error=%s", user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    plan.invitation = invitation_service.create_invite(plan.id)

    try:
        plan.save()
    except Exception as e:
        logger.exception("create_plan invite save failed plan_id=%s error=%s", plan.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    logger.info("create_plan created plan_id=%s organizer_id=%s", plan.id, user.id)
    return plan

def get_plans(user):
    plans = Plan.objects(Q(organizer=user) | Q(participants=user))

    return plans

def get_public_plans():
    plans = Plan.objects(is_public=True)

    return plans

def get_plan(plan_id, user=None):
    plan = Plan.objects(id=plan_id).first() 
    if not plan:
        logger.warning("get_plan not found plan_id=%s", plan_id)
        raise PlanNotFound(plan_id)
    if user and not plan.is_public:
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
        logger.exception("lock_plan save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def update_plan(plan, user, data):
    if user != plan.organizer:
        raise NotPlanOrganizer
    
    for field in PLAN_ALLOWED_FIELDS.keys():
        if field in data:
            if field == 'image_key':
                setattr(plan, 'image', None)    
                setattr(plan, 'stock_image', data[field])    
            if field == 'image_id': # TODO - Update with image service logic
                setattr(plan, 'stock_image', None)
                setattr(plan, 'image', data[field])        
            else:
                setattr(plan, field, data[field])

    try:    
        plan.save()
    except Exception as e:
        logger.exception("update_plan save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def delete_plan():
    pass

def create_activity(plan, proposer, data):
    if plan.status != 'active':
        raise UserNotAuthorized
    if plan.is_open and (proposer != plan.organizer or proposer not in plan.admins):
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
        logger.exception("create_activity save failed plan_id=%s error=%s", plan.id, str(e))
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
        logger.exception(
            "update_activity save failed plan_id=%s activity_id=%s error=%s",
            plan.id,
            activity.activity_id,
            str(e),
        )
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

    # Organizer is already marked as "paid"
    if plan.organizer in activity.votes:
        activity.payments.append(plan.organizer)
        plan.costs.collected += activity.costs.per_person

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
        logger.exception("lock_activity save failed plan_id=%s activity_id=%s error=%s", plan.id, activity_id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return activity

def add_participant(plan, user):
    plan.participants.append(user)
    try:
        plan.save()
    except Exception as e:
        logger.exception("add_participant save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def add_admin(plan, organizer, user):
    if organizer != plan.organizer:
        raise NotPlanOrganizer
    if user not in plan.participants:
        raise UserNotFound(user.id)
    
    if user not in plan.admins:
        plan.participants.remove(user)
        plan.admins.append(user)
    try:
        plan.save()
    except Exception as e:
        logger.exception("add_participant save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
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
        logger.exception(
            "remove_participant save failed plan_id=%s participant_id=%s error=%s",
            plan.id,
            participant_id,
            str(e),
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan

def vote_activity(plan, user, activity_id):
    activity = next(
        (a for a in plan.activities if a.activity_id == activity_id),
        None)
    if not activity:
        raise ActivityNotFound
    if user != plan.organizer and user not in plan.admins and user not in plan.participants:
        raise UserNotAuthorized
    
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
        logger.exception("vote_activity save failed plan_id=%s activity_id=%s error=%s", plan.id, activity_id, str(e))
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
        logger.exception("send_message save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
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
        logger.exception("pay save failed plan_id=%s user_id=%s error=%s", plan.id, user.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan


def is_member(plan_id, user):
    plan = Plan.objects(id=plan_id).first()
    if not plan:
        return False
    if user not in plan.participants and user != plan.organizer:
        return False
    return True

def update_image(plan, image):
    plan.image = image
    plan.stock_image = None

    try:
        plan.save()
    except Exception as e:
        logger.exception("update_image save failed plan_id=%s image_id=%s error=%s", plan.id, image.id, str(e))
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    return plan
