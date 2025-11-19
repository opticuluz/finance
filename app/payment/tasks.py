from celery import shared_task
from PIL import Image
from io import BytesIO
import boto3
import os
from django.conf import settings


@shared_task
def compress_receipt(file_key):
    from payment.models import PaymentReceipt

    # Работаем напрямую с MinIO через boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    bucket = settings.AWS_STORAGE_BUCKET_NAME

    # Загружаем оригинал
    obj = s3.get_object(Bucket=bucket, Key=file_key)
    img = Image.open(obj["Body"])

    # Конвертируем в RGB/RGBA для корректного сохранения
    if img.mode in ("RGBA", "LA"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Сжимаем → WEBP
    buf = BytesIO()
    img.save(
        buf,
        format="WEBP",
        quality=60,
        method=6,
        optimize=True
    )
    buf.seek(0)

    # Новый ключ с расширением .webp
    base, _ = os.path.splitext(file_key)
    new_key = f"{base}.webp"

    # Загружаем новый файл в S3/MinIO
    s3.put_object(
        Bucket=bucket,
        Key=new_key,
        Body=buf,
        ContentType="image/webp",
        ACL="private"
    )

    # Удаляем старый файл
    s3.delete_object(Bucket=bucket, Key=file_key)

    # Обновляем модель PaymentReceipt
    try:
        receipt = PaymentReceipt.objects.get(image=file_key)
        receipt.image.name = new_key
        receipt.save(update_fields=["image"])
    except PaymentReceipt.DoesNotExist:
        pass

    return new_key
