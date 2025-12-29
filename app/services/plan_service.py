from app.services import invitation_service
from app.models.plan import Plan

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

def create_activity():
    pass

def update_activity():
    pass

def delete_activity():
    pass

def vote_activity():
    pass

def send_message():
    pass








