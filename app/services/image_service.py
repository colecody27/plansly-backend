import os 
from app.errors import ValidationError, DatabaseError, ImageNotFound
from datetime import datetime, timezone 
import uuid
from app.extensions import s3
from app.models.image import Image
from app.services import audit_service
from app.constants import Resource, Status, Action
from app.logger import get_logger

BUCKET = os.environ["AWS_S3_BUCKET_NAME"]
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_FILE_TYPES = {"image/jpeg", "image/png", "image/webp"}

logger = get_logger(__name__)

def get_upload_url(user, data):
    filename = data.get('filename')
    filetype = data.get('filetype')
    filesize = data.get('filesize')

    if filesize > MAX_IMAGE_SIZE:
        logger.warning("get_upload_url file too large user_id=%s size=%s", user.id, filesize)
        raise ValidationError
    
    if filetype not in ALLOWED_FILE_TYPES:
        logger.warning("get_upload_url invalid filetype user_id=%s filetype=%s", user.id, filetype)
        raise ValidationError

    filename = filename.replace('/', '_').replace('\\', '_')
    curr_date = datetime.now(timezone.utc)
    year, month, day = curr_date.year, curr_date.month, curr_date.day
    expires_in = 60
    u_url_id = uuid.uuid4()

    s3_key = f'uploads/{year}/{month}/{day}/user/{str(user.id)}/{u_url_id}'

    image = create_image(user, filename, filetype, filesize, s3_key)
    
    pre_signed_url = s3.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            "Bucket": BUCKET,
            "Key": s3_key,
            "ContentType": filetype
        },
        ExpiresIn=expires_in
    )
    return pre_signed_url, image

def create_image(user, name, type, size, key):
    image = Image(
        filename = name,
        filesize = size,
        filetype = type,
        key = key,
        uploaded_by = user
    )
    try:
        image.save()
    except Exception as e:
        logger.exception("create_image save failed user_id=%s key=%s error=%s", user.id, key, str(e))
        audit_service.log_event(
            actor_id=str(user.id),
            resource_type=Resource.PROFILE,
            resource_id=None,
            event_type=Action.CREATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=None,
            after=None,
            idempotency_key=f"{user.id}:image:{key}:create",
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(user.id),
        resource_type=Resource.PROFILE,
        resource_id=str(image.id),
        event_type=Action.CREATE,
        status=Status.SUCCESS,
        error_message=None,
        before=None,
        after=image.to_dict(),
        idempotency_key=f"{user.id}:image:{key}:create",
    )
    
    return image

def get_image(id, plan=None):
    try:
        image = Image.objects(id=id).first()
    except Exception as e:
        logger.exception("get_image lookup failed image_id=%s error=%s", id, str(e))
        raise ImageNotFound
    return image

def image_uploaded(image):
    before = image.to_dict()
    image.upload_status = 'uploaded'

    try:
        image.save()
    except Exception as e:
        logger.exception("image_uploaded save failed image_id=%s error=%s", image.id, str(e))
        audit_service.log_event(
            actor_id=str(getattr(image.uploaded_by, "id", "system")),
            resource_type=Resource.PROFILE,
            resource_id=str(image.id),
            event_type=Action.UPDATE,
            status=Status.FAILURE,
            error_message=str(e),
            before=before,
            after=None,
            idempotency_key=f"image:{image.id}:uploaded",
        )
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    audit_service.log_event(
        actor_id=str(getattr(image.uploaded_by, "id", "system")),
        resource_type=Resource.PROFILE,
        resource_id=str(image.id),
        event_type=Action.UPDATE,
        status=Status.SUCCESS,
        error_message=None,
        before=before,
        after=image.to_dict(),
        idempotency_key=f"image:{image.id}:uploaded",
    )


def get_download_url(key):    
    pre_signed_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            "Bucket": BUCKET,
            "Key": key,
        },
        ExpiresIn=60
    )
    return pre_signed_url

def get_download_urls(image):
    return []
    pre_signed_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            "Bucket": BUCKET,
            "Key": image.key,
        },
        ExpiresIn=60
    )
    return pre_signed_url, image
