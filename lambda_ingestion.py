import json
import boto3
import awswrangler as wr
import pandas
import numpy as np
import ast
from io import BytesIO
import ast

s3 = boto3.resource('s3')

"""

GHActions update test string

"""

def get_objects_names_from_bucket(bucket, prefix=None):
    s3_bucket = s3.Bucket(bucket)
    list_of_file_names = []
    output_dict = {}

    if prefix is not None:
        for el in s3_bucket.objects.filter(Prefix=prefix):
            name = el.key.split('/')[-1]
            if name == 'yelp_academic_dataset_business.json':
                list_of_file_names.append(name)
    else:
        for el in s3_bucket.objects.all():
            if el.key.endswith(('.json')):
                name = el.key
                list_of_file_names.append(name)

    output_dict.update({bucket: list_of_file_names})
    return output_dict


def read_from_s3(input_dict, prefix):
    output_dict = {}
    list_of_dicts = []

    for bucket, file_names in input_dict.items():
        for filename in file_names:
            name_to_read = prefix + filename
            obj = s3.Object(bucket, name_to_read)
            bbb = obj.get()['Body'].read()

            with BytesIO(bbb) as bio:
                df = pandas.DataFrame(bio)
                dic = df.to_dict()
                for i in range(len(dic[0])):
                    js = json.loads(dic[0][i].decode('utf-8'))
                    list_of_dicts.append(js)
            list_of_dicts = transform_business_hours_to_table_view(list_of_dicts)

            output_dict.update({filename: list_of_dicts})

    df = pandas.DataFrame(output_dict['yelp_academic_dataset_business.json'])

    return df


def write_to_s3(bucket, data, output_prefix='/'):
    wr.s3.to_parquet(df=data, path=f's3://{bucket}{output_prefix}business.parquet')


def transform_business_hours_to_table_view(list_of_dicts):
    data = list_of_dicts

    hours_none = {'Monday': None, 'Tuesday': None, 'Wednesday': None, 'Thursday': None, 'Friday': None,
                  'Saturday': None, 'Sunday': None}
    replacement_keys = {
        'Monday': 'working_hours_monday',
        'Tuesday': 'working_hours_tuesday',
        'Wednesday': 'working_hours_wednesday',
        'Thursday': 'working_hours_thursday',
        'Friday': 'working_hours_friday',
        'Saturday': 'working_hours_saturday',
        'Sunday': 'working_hours_sunday',
    }
    full_hours = {}

    for n in range(len(data)):
        if data[n]['hours'] is None or 'hours' not in data[n].keys():
            data[n].update(hours_none)
        else:
            full_hours.update(hours_none)
            full_hours.update(data[n]['hours'])
            data[n].update(full_hours)
            data[n].pop('hours')
    data = [{replacement_keys.get(k, k): v for k, v in data[n].items()} for n in range(len(data))]
    return data


def lambda_handler(event, context):
    # Input parameters
    bucket_name = 'ts-mybucket-03'
    read_prefix = 'yelp/'
    dest_prefix = '/yelp_ready_to_load/'

    from_s3 = get_objects_names_from_bucket(bucket_name, read_prefix)
    data = read_from_s3(from_s3, read_prefix)
    write_to_s3(bucket_name, data, dest_prefix)

    return {
        'statusCode': 200,
        'body': '    ----    >>>>    yelp_academic_dataset_business.json successfully converted to Business.json and Attributes.json'
    }
