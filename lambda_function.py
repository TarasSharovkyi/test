"""
Something will be written here later...
"""
import os
import time
import json
import datetime
from datetime import date
import boto3
from load_layer.s3_loader import S3Loader
from load_layer.rds_loader import RDSLoader
from extract_layer.autoria_reader import AutoRiaReader
from extract_layer.s3_reader import S3Reader
from transform_layer.processor import Processor


def get_app_execution_data(today, start_time: float, cars: list) -> dict:
    """
    This is a helper method.
    Its purpose is to calculate
    the execution time of the script.
    """
    exec_date = today.strftime("%m-%d-%y")
    exec_time = time.time() - start_time

    return {'date': exec_date,
            'amount of cars': len(cars),
            'exec_time': round(exec_time, 4)}


def lambda_handler(event, context):
    """
    Something will be written here later...
    """
    today = date.today()
    my_date = datetime.date.today()
    week_num = my_date.isocalendar()
    s3_resource = boto3.resource('s3')
    # script start time
    start_time = time.time()

    # executing methods to extract the required data from S for other methods to work
    all_engine_types = S3Reader() \
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=os.environ['S3_BUCKET'],
                          object_name='all_engine_types')
    all_gearbox_types = S3Reader() \
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=os.environ['S3_BUCKET'],
                          object_name='all_gearbox_types')
    two_word_car_brands = S3Reader() \
        .get_data_from_s3(s3_resource=s3_resource,
                          s3_bucket=os.environ['S3_BUCKET'],
                          object_name='two_word_car_brands')

    # extract data about all items from the source
    cars = AutoRiaReader().process_data_to_tableview(my_date=my_date,
                                                     week_num=week_num,
                                                     all_engine_types=all_engine_types,
                                                     two_word_car_brands=two_word_car_brands)

    # Processor layer in action
    Processor().translate_engine_type(cars=cars,
                                      all_engine_types=all_engine_types)
    Processor().translate_gearbox_type(cars=cars,
                                       all_gearbox_types=all_gearbox_types)

    # data transformations
    Processor().translate_engine_type(cars=cars,
                                      all_engine_types=all_engine_types)
    Processor().translate_gearbox_type(cars=cars,
                                       all_gearbox_types=all_gearbox_types)

    # script execution data: date, amount of cars, execution time
    exec_data = get_app_execution_data(today=today,
                                       start_time=start_time,
                                       cars=cars)

    # Load daily data to S3
    S3Loader().write_daily_to_s3(bucket=os.environ['S3_BUCKET'],
                                 prefix='ara/data',
                                 object_name=today.strftime("%m-%d-%y"),
                                 data_to_write=cars)
    S3Loader().write_daily_to_s3(bucket=os.environ['S3_BUCKET'],
                                 prefix='ara/exec',
                                 object_name=today.strftime("%m-%d-%y"),
                                 data_to_write=exec_data)

    # load daily data to RDS
    connection = RDSLoader().get_rds_connection(host=os.environ['DB_HOST'],
                                                database=os.environ['DATABASE'],
                                                user=os.environ['DB_USER'],
                                                password=os.environ['DB_PASSWORD'])
    RDSLoader().load_to_rds(connection=connection,
                            table=os.environ['TABLE'],
                            cars=cars)

    return {
        'statusCode': 200,
        'body': json.dumps(f'    ---->>>> EXECUTION DETAILS  {exec_data}. '
                           f'EVENT---->>>>  {event}. '
                           f'CONTEXT---->>>>  {context}')
    }
