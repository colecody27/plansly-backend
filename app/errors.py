class AppError(Exception):
    """Base class for all custom application exceptions."""
    status_code = 500
    error_code = 'app_error'

    def __init__(self, message=None, *, details=None):
        super().__init__(message or 'Application error')
        self.message = message or 'Application error'
        self.details = details

# ===== Generic HTTP error categories =====
class NotFound(AppError):
    status_code = 404
    error_code = 'not_found'

class Unauthorized(AppError):
    status_code = 401
    error_code = 'unauthorized'

class Forbidden(AppError):
    status_code = 403
    error_code = 'forbidden'

class DatabaseError(AppError):
    status_code = 500
    error_code = 'database_error'

    def __init__(self, message="Database operation failed", *, details=None):
        super().__init__(message=message, details=details)

class ValidationError(AppError):
    status_code = 400
    error_code = "validation_error"

    def __init__(self, message="Invalid parameters", *, details=None):
        super().__init__(message=message, details=details)

# ===== Domain-specific errors =====
# Users
class UserNotFound(NotFound):
    def __init__(self, uid):
        super().__init__(
            message=f'User with ID "{uid}" not found',
            details={'user_id': uid}
        )

class UserNotAuthorized(Forbidden):
    def __init__(self, uid):
        super().__init__(
            message=f'User with ID "{uid}" is not authorized to perform this action',
            details={'user_id': uid}
        )

# Plans
class PlanNotFound(NotFound):
    def __init__(self, plan_id):
        super().__init__(
            message=f'Plan with ID "{plan_id}" not found',
            details={'plan_id': plan_id}
        )

class NotPlanOrganizer(Forbidden):
    def __init__(self):
        super().__init__(
            message='Only the organizer of the plan can perform this action'
        )

class ActivityNotFound(NotFound):
    def __init__(self, activity_id):
        super().__init__(
            message=f'Activity with ID "{activity_id}" not found',
            details={'plan_id': activity_id}
        )

# Invitations
class InviteNotFound(NotFound):
    def __init__(self, invite_id):
        super().__init__(
            message=f'Invitation with ID "{invite_id}" not found',
            details={'invite_id': invite_id}
        )

class InviteExpired(Forbidden):
    def __init__(self, expires_at=None):
        msg = 'This invitation link has expired'
        details = {'expires_at': expires_at} if expires_at else None
        super().__init__(message=msg, details=details)

