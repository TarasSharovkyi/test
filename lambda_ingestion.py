"""
SOMETHING
"""
import os
import time
import json
import datetime
from datetime import date
import boto3
from load_layer import s3_logic, rds_logic
from extract_layer import source_reader
from transform_layer import processor


def get_app_execution_data(today, start_time: float, cars: list) -> dict:
    """
    this is a helper method.
    Its purpose is to collect script execution data
    into a dictionary for further use
    """
    exec_date = today.strftime("%m-%d-%y")
    exec_time = time.time() - start_time

    return {'date': exec_date, 'amount of cars': len(cars), 'exec_time': round(exec_time, 4)}


def lambda_handler(event, context):
    """
    SOMETHING
    """
    # database credentials
    database_host = os.environ['DB_HOST']
    database = os.environ['DATABASE']
    database_user = os.environ['DB_USER']
    database_pass = os.environ['DB_PASSWORD']
    database_port = os.environ['DB_PORT']
    table = os.environ['TABLE']
    today = date.today()
    my_date = datetime.date.today()
    week_num = my_date.isocalendar()
    current_date = today.strftime("%m-%d-%y")
    s3_bucket = os.environ['S3_BUCKET']
    s3_resource = boto3.resource('s3')
    # script start time
    start_time = time.time()


    # executing methods to extract the required data from S for other methods to work
    all_engine_types = s3_logic\
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=s3_bucket,
                          object_name='all_engine_types')
    all_gearbox_types = s3_logic\
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=s3_bucket,
                          object_name='all_gearbox_types')
    two_word_car_brands = s3_logic\
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=s3_bucket,
                          object_name='two_word_car_brands')


    # extract data about all items from the source
    cars = source_reader.process_data_to_tableview(today=today,
                                                   my_date=my_date,
                                                   week_num=week_num,
                                                   all_engine_types=all_engine_types,
                                                   two_word_car_brands=two_word_car_brands)


    # Processor layer in action
    processor.translate_engine_type(cars=cars, all_engine_types=all_engine_types)
    processor.translate_gearbox_type(cars=cars, all_gearbox_types=all_gearbox_types)


    # data transformations
    processor.translate_engine_type(cars=cars, all_engine_types=all_engine_types)
    processor.translate_gearbox_type(cars=cars, all_gearbox_types=all_gearbox_types)

    # script execution data: date, amount of cars, execution time
    exec_data = get_app_execution_data(today, start_time, cars)

    # Load daily data to S3
    s3_logic.write_daily_to_s3(s3_resource=s3_resource, bucket=s3_bucket,
                               prefix='ara/data', object_name=current_date,
                               data_to_write=cars, week_number=week_num[1])
    s3_logic.write_daily_to_s3(s3_resource=s3_resource, bucket=s3_bucket,
                               prefix='ara/exec', object_name=current_date,
                               data_to_write=exec_data, week_number=week_num[1])


    # load daily data to RDS
    connection = rds_logic.get_rds_connection(host=database_host, database=database,
                                              user=database_user, password=database_pass,
                                              port=database_port)
    rds_logic.load_to_rds(connection=connection, table=table, cars=cars)


    return {
        'statusCode': 200,
        'body': json.dumps(f'    ---->>>> EXECUTION DETAILS  {exec_data}. '
                           f'EVENT---->>>>  {event}. '
                           f'CONTEXT---->>>>  {context}')
    }
