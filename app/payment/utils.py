import boto3
from botocore.client import Config
from django.conf import settings
from urllib.parse import urlparse, urlunparse


def get_presigned_url(key, expires_in=3600):

    internal_endpoint = settings.AWS_S3_ENDPOINT_URL

    if settings.DEBUG:
        final_scheme = "http"
    else:
        final_scheme = "https"

    public_netloc = settings.MINIO_PUBLIC_DOMAIN

    s3 = boto3.client(
        "s3",
        endpoint_url=internal_endpoint,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(s3={'addressing_style': 'path'})
    )

    url = s3.generate_presigned_url(
        "get_object",
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
        ExpiresIn=expires_in
    )

    parsed = urlparse(url)
    parsed = parsed._replace(
        scheme=final_scheme,
        netloc=public_netloc
    )

    return urlunparse(parsed)
