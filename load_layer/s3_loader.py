"""
ALL S3 LOGIC
"""
import json
import datetime
import boto3


class S3Loader:
    """
    Something will be written here later...
    """
    s3_resource = boto3.resource('s3')
    week_number = datetime.date.today().isocalendar()[1]

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

    def write_daily_to_s3(self, bucket: str, prefix: str,
                          object_name: str, data_to_write: [list, dict]):
        """
        the goal of this method is to write data to S3 bucket as json objects
        """
        self.s3_resource.Bucket(bucket)\
            .put_object(Key=f'daily_data/{prefix}/week_#{self.week_number}/{object_name}.json',
                        Body=json.dumps(data_to_write,
                                        indent=4))
