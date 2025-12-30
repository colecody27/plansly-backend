from app.services import invitation_service
from app.models.plan import Plan
from app.models.user import User
from app.models.activity import Activity

def create_plan(data):
    try:
        plan = Plan(
            name=data.get('name'),
            description=data.get('description'),
            type=data.get('type'),
            organizer_id=data.get('organizer_id'),
            deadline=data.get('deadline'),
            theme=data.get('theme'),
        )
        plan.save()
        
    except Exception as e:
        print(e)
        return {'error': 'Error creating plan'}
    plan.invitation_id = invitation_service.create_invite(plan.id).id
    plan.save()
    return plan

def update_plan():
    pass 

def delete_plan():
    pass

def create_activity(data, proposer, plan):
    try:
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
        plan.save()
    except Exception as e:
        return {'error': 'Error creating activity'}
    return {'success': activity}

def update_activity():
    pass

def delete_activity():
    pass

def vote_activity():
    pass

def send_message():
    pass








