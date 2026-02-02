import os 
from app.errors import ValidationError, DatabaseError, ImageNotFound
from datetime import datetime, timezone 
import uuid
from app.extensions import s3
from app.models.image import Image

BUCKET = os.environ["AWS_S3_BUCKET_NAME"]
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_FILE_TYPES = {"image/jpeg", "image/png", "image/webp"}

def get_upload_url(user, data):
    filename = data.get('filename')
    filetype = data.get('filetype')
    filesize = data.get('filesize')

    if filesize > MAX_IMAGE_SIZE:
        raise ValidationError
    
    if filetype not in ALLOWED_FILE_TYPES:
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
    print(f'Presigned URL: {pre_signed_url}')
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
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})
    
    return image

def get_image(id, plan=None):
    try:
        image = Image.objects(id=id).first()
    except Exception as e:
        raise ImageNotFound
    return image

def image_uploaded(image):
    image.upload_status = 'uploaded'

    try:
        image.save()
    except Exception as e:
        raise DatabaseError("Unexpected database error", details={"exception": str(e)})


def get_download_url(key):    
    pre_signed_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            "Bucket": BUCKET,
            "Key": key,
        },
        ExpiresIn=60
    )
    print(f'Presigned URL: {pre_signed_url}')
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
    print(f'Presigned URL: {pre_signed_url}')
    return pre_signed_url, image

