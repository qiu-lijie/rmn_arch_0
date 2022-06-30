from storages.backends.s3boto3 import S3StaticStorage

class StaticStorage(S3StaticStorage):
    """
    Sepcify location for the sole purpose of seperating static from media files
    """
    location = 'static'
