"""
ALL S3 LOGIC
"""
import json


def get_data_from_s3(s3_resource, s3_bucket: str, object_name: str) -> dict:
    """
    some data is stored in S3 bucket.
    This method extracts it from there and returns it in the required format
    """
    obj = s3_resource.Object(bucket_name=s3_bucket, key=f'src/{object_name}.json').get()
    data = obj['Body'].read().decode('utf-8')
    data = json.loads(data)

    return data


def write_daily_to_s3(s3, bucket: str, prefix: str, object_name: str, data_to_write: [list, dict], week_number: int):
    """
    the goal of this method is to write data to S3 bucket as json objects
    """
    s3.Bucket(bucket).put_object(Key=f'daily_data/{prefix}/week_#{week_number}/{object_name}.json',
                                 Body=json.dumps(data_to_write, indent=4))