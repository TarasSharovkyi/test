from io import BytesIO
import json
import awswrangler as wr
import boto3
import pandas

s3 = boto3.resource('s3')


def get_objects_names_from_bucket(bucket, prefix=None):
    """
    docstring
    """
    s3_bucket = s3.Bucket(bucket)
    list_of_file_names = []
    output_dict = {}

    if prefix is not None:
        for element in s3_bucket.objects.filter(Prefix=prefix):
            name = element.key.split('/')[-1]
            if name == 'yelp_academic_dataset_business.json':
                list_of_file_names.append(name)
    else:
        for element in s3_bucket.objects.all():
            if element.key.endswith(('.json')):
                name = element.key
                list_of_file_names.append(name)

    output_dict.update({bucket: list_of_file_names})
    return output_dict


def read_from_s3(input_dict, prefix):
    """
    docstring
    """
    output_dict = {}
    list_of_dicts = []

    for bucket, file_names in input_dict.items():
        for filename in file_names:
            name_to_read = prefix + filename
            obj = s3.Object(bucket, name_to_read)
            bbb = obj.get()['Body'].read()

            with BytesIO(bbb) as bio:
                dataframe = pandas.DataFrame(bio)
                dic = dataframe.to_dict()
                for i in range(len(dic[0])):
                    data_json = json.loads(dic[0][i].decode('utf-8'))
                    list_of_dicts.append(data_json)
            list_of_dicts = transform_business_hours_to_table_view(list_of_dicts)

            output_dict.update({filename: list_of_dicts})

    dataframe = pandas.DataFrame(output_dict['yelp_academic_dataset_business.json'])

    return dataframe


def write_to_s3(bucket, data, output_prefix='/'):
    """
    docstring
    """
    wr.s3.to_parquet(df=data, path=f's3://{bucket}{output_prefix}business.parquet')


def transform_business_hours_to_table_view(list_of_dicts):
    """
    docstring
    """
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

    for index in range(len(data)):
        if data[index]['hours'] is None or 'hours' not in data[index].keys():
            data[index].update(hours_none)
        else:
            full_hours.update(hours_none)
            full_hours.update(data[index]['hours'])
            data[index].update(full_hours)
            data[index].pop('hours')
    data = [{replacement_keys.get(k, k): v for k, v in data[n].items()} for n in range(len(data))]
    return data


def lambda_handler():
    """
    docstring
    """
    # Input parameters
    bucket_name = 'ts-mybucket-03'
    read_prefix = 'yelp/'
    dest_prefix = '/yelp_ready_to_load/'

    from_s3 = get_objects_names_from_bucket(bucket_name, read_prefix)
    data = read_from_s3(from_s3, read_prefix)
    write_to_s3(bucket_name, data, dest_prefix)

    return {
        'statusCode': 200,
        'body': '    ----    >>>>    yelp_academic_dataset_business.json '
                'successfully converted to Business.json and Attributes.json'
    }
