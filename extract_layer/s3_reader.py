"""
Something will be written here later...
"""
import json
import boto3


class S3Reader:
    """
    Something will be written here later...
    """
    s3_resource = boto3.resource('s3')

    def get_data_from_s3(self, s3_bucket: str, object_name: str) -> dict:
        """
        some data is stored in S3 bucket.
        This method extracts it from there and returns it in the required format
        """
        obj = self.s3_resource.Object(bucket_name=s3_bucket,
                                 key=f'src/{object_name}.json').get()
        data = obj['Body'].read().decode('utf-8')
        data = json.loads(data)

        return data