import os
import calendar
import time
import re
import json
import datetime
from datetime import date
import requests
from bs4 import BeautifulSoup
import boto3
import psycopg2


def translate_engine_type(cars: list, all_engine_types: dict) -> list:
    """
    this method replaces cyrillic engine fuel type to English
    """
    for car in cars:
        for key, value in car.items():
            if key == 'engine_type' and value in all_engine_types.keys():
                value = all_engine_types[value]
                car.update({key: value})

    return cars


def translate_gearbox_type(cars: list, all_gearbox_types: dict) -> list:
    """
    this method replaces cyrillic gearbox type to English
    """
    for car in cars:
        for key, value in car.items():
            if key == 'gearbox_type' and value in all_gearbox_types.keys():
                value = all_gearbox_types[value]
                car.update({key: value})

    return cars


def get_brand_model_from_item(item, two_word_car_brands: dict) -> dict:
    """
    this method extracts car brand and car model from the car element
    """
    car_item = item.find('span', class_='blue bold').text
    brand_model_year = car_item.split()

    if brand_model_year[0] in two_word_car_brands.keys():
        correct_brand = two_word_car_brands[brand_model_year[0]]
        model = ' '.join(brand_model_year[2:])
    else:
        correct_brand = brand_model_year[0]
        model = ' '.join(brand_model_year[1:])

    return {'brand': correct_brand, 'model': model}


def get_data_from_source(page_number: int):
    """
    Parser method
    """
    requested_data = requests.get(
        f'https://auto.ria.com/uk/search/'
        f'?indexName=auto&categories.main.id=1&country.import.usa.not=-1&price.currency=1'
        f'&top=2&abroad.not=0&custom.not=-1&page={page_number}&size=100'
    )

    soup = BeautifulSoup(requested_data.content, 'html.parser')
    items = soup.body.find("div", class_='app-content').find_all("section", class_='ticket-item')

    return items


def process_data_to_tableview(today, my_date, week_num: int,
                              all_engine_types: dict, two_word_car_brands: dict):
    """
    this method extracts data from a source,
    transforms engine types, gearbox types, 2-word brand names etc.
    and returns a list of dicts with all items for the current day.
    """

    cars = []
    page_number = 0

    while True:

        items = get_data_from_source(page_number=page_number)

        if len(items) != 0:
            for item in items:

                car_brand_and_model_list = get_brand_model_from_item(item, two_word_car_brands)

                mileage = re.findall('[0-9]+', str.lstrip(item.find('li', class_='item-char js-race').text))

                year = str.strip(item.find('a', class_='address').text)

                mileage_loc_engine_gear = re.split('s{3,}',
                                                   str.strip(item.find('ul', class_="unstyle characteristic").text))

                engine_volume = mileage_loc_engine_gear[2].split(', ')
                if len(engine_volume) < 2:
                    if engine_volume[0] in all_engine_types.keys():
                        engine_type = engine_volume[0]
                        volume = 0.0
                    else:
                        volume = engine_volume[:2]
                        volume = volume[-1].split()
                        volume = float(volume[0])
                        engine_type = 'Not specified'
                else:
                    engine_type = engine_volume[0]
                    volume = engine_volume[1].split()
                    volume = float(volume[0])

                location = str.strip(item.find('li', class_='item-char view-location js-location').text)

                price = str.replace(item.find('span', class_='size15').text, ' ', '').split('$')

                cars.append({
                    'week_number': week_num,
                    'date': today.strftime("%m-%d-%y"),
                    'day_of_week': calendar.day_name[my_date.weekday()],
                    'link': item.find('a', class_='m-link-ticket').get('href'),
                    'brand': car_brand_and_model_list['brand'],
                    'model': car_brand_and_model_list['model'],
                    'year_of_manufacture': int(year[-4:]),
                    'price_usd': int(price[0]),
                    'mileage': int(mileage[0]) * 1000,
                    'engine_type': engine_type,
                    'engine_volume': volume,
                    'gearbox_type': mileage_loc_engine_gear[-1],
                    'location': location[:-8]
                })
            page_number += 1
        else:
            break

    return cars


def write_daily_to_s3(s3_resource, bucket: str, prefix: str,
                      object_name: str, data_to_write: [list, dict], week_number: int):
    """
    the goal of this method is to write data to S3 bucket as json objects
    """
    s3_resource.Bucket(bucket).put_object(Key=f'daily_data/{prefix}/week_#{week_number}/{object_name}.json',
                                 Body=json.dumps(data_to_write, indent=4))


def get_app_execution_data(today, start_time: float, cars: list) -> dict:
    """
    this is a helper method. Its purpose is to
    collect script execution data into a dictionary for further use
    """
    exec_date = today.strftime("%m-%d-%y")
    exec_time = time.time() - start_time

    return {'date': exec_date, 'amount of cars': len(cars), 'exec_time': round(exec_time, 4)}


def get_rds_connection(host: str, database: str, user: str, password: str, port: str):
    """
    This method creates and returns database connection
    """
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)

    return connection


def load_to_rds(connection, table: str, cars: list):
    """
    A method for working with a database.
    The presence of the table in the database is checked and,
    if necessary, a creation query is executed.
    A query to write data to the database
    in the specified table is also executed.
    """
    crate_table_query = f'CREATE TABLE IF NOT EXISTS {table} ' \
                        f'(date varchar(10), day_of_week varchar(25), week_number integer, link varchar(255), ' \
                        f'brand varchar(255), model varchar(255), year_of_manufacture integer, engine_type varchar(50), ' \
                        f'engine_volume float, gearbox_type varchar(50), mileage integer, price_usd integer, ' \
                        f'location varchar(255), PRIMARY KEY(link))'

    try:
        # Get cursor object from the database connection
        cur = connection.cursor()
        # Creates a table if it does not exist in the database with 'link' as Primary Key
        cur.execute(crate_table_query)
        # INSERT all daily data into table and ignore 'link' duplicates
        for car in cars:
            cur.execute(
                f'INSERT INTO {table} (date, day_of_week, week_number, link, brand, model, year_of_manufacture, '
                f'engine_type, engine_volume, gearbox_type, mileage, price_usd, location) '
                f'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                f'ON CONFLICT (link) DO NOTHING',
                (car['date'], car['day_of_week'], car['week_number'], car['link'], car['brand'], car['model'],
                 car['year_of_manufacture'],
                 car['engine_type'], car['engine_volume'], car['gearbox_type'], car['mileage'], car['price_usd'],
                 car['location']))
        # Close cursor object
        cur.close()
        # Save all the modifications made since the last commit
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print(f'ERROR --------->>>>    Failed to connect to Database! -->>  {error}')


def get_data_from_s3(s3_resource, s3_bucket: str, object_name: str) -> dict:
    """
    some data is stored in S3 bucket.
    This method extracts it from there and returns it in the required format
    """
    obj = s3_resource.Object(bucket_name=s3_bucket, key=f'src/{object_name}.json').get()
    data = obj['Body'].read().decode('utf-8')
    data = json.loads(data)

    return data


def lambda_handler():
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
    # script start time
    start_time = time.time()

    today = date.today()
    my_date = datetime.date.today()
    week_num = my_date.isocalendar()
    current_date = today.strftime("%m-%d-%y")
    s3_bucket = os.environ['S3_BUCKET']
    s3_resource = boto3.resource('s3')

    # executing methods to extract the required data from S for other methods to work
    all_engine_types = get_data_from_s3(s3_resource=s3_resource, s3_bucket=s3_bucket, object_name='all_engine_types')
    all_gearbox_types = get_data_from_s3(s3_resource=s3_resource, s3_bucket=s3_bucket, object_name='all_gearbox_types')
    two_word_car_brands = get_data_from_s3(s3_resource=s3_resource, s3_bucket=s3_bucket, object_name='two_word_car_brands')

    # extract data about all items from the source
    cars = process_data_to_tableview(today, my_date, week_num=week_num.week, all_engine_types=all_engine_types,
                                     two_word_car_brands=two_word_car_brands)

    # data transformations
    translate_engine_type(cars, all_engine_types)
    translate_gearbox_type(cars, all_gearbox_types)

    # script execution data: date, amount of cars, execution time
    exec_data = get_app_execution_data(today, start_time, cars)

    # Load daily data to S3
    write_daily_to_s3(s3_resource=s3_resource, bucket=s3_bucket, prefix='data', object_name=current_date, data_to_write=cars,
                      week_number=week_num.week)
    write_daily_to_s3(s3_resource=s3_resource, bucket=s3_bucket, prefix='exec', object_name=current_date, data_to_write=exec_data,
                      week_number=week_num.week)

    # load daily data to RDS
    connection = get_rds_connection(host=database_host, database=database, user=database_user, password=database_pass,
                                    port=database_port)
    load_to_rds(connection=connection, table=table, cars=cars)

    return {
        'statusCode': 200,
        'body': json.dumps(f'    ---->>>> EXECUTION DETAILS    ---->>>>    {exec_data}')
    }
