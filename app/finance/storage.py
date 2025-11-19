from storages.backends.s3boto3 import S3Boto3Storage


class ReceiptStorage(S3Boto3Storage):
    location = ""
    default_acl = "private"
