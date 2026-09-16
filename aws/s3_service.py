import boto3

from config import Config


class S3Service:
    """
    Handles document storage operations in Amazon S3.
    """

    def __init__(self):
        self.bucket_name = Config.S3_BUCKET_NAME

        self.s3_client = boto3.client(
            "s3",
            region_name=Config.AWS_REGION
        )

    def upload_file(self, file_path, object_key):
        """
        Upload a local file to the LexiGuard S3 bucket.
        """

        self.s3_client.upload_file(
            file_path,
            self.bucket_name,
            object_key
        )

        return {
            "bucket": self.bucket_name,
            "object_key": object_key
        }

    def download_file(self, object_key, local_file_path):
        """
        Download a file from S3 to a temporary local path.
        """

        self.s3_client.download_file(
            self.bucket_name,
            object_key,
            local_file_path
        )

        return local_file_path

    def file_exists(self, object_key):
        """
        Check whether an object exists in the S3 bucket.
        """

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            return True

        except self.s3_client.exceptions.ClientError:
            return False