"""
SOMETHING
"""
from bs4 import BeautifulSoup
import requests
import re
import calendar
import datetime
from datetime import date


def process_data_to_tableview(today, my_date, week_num: int, all_engine_types: dict, two_word_car_brands: dict):
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
                mileage_loc_engine_gear = re.split('\s{3,}',
                                                   str.strip(item.find('ul', class_="unstyle characteristic").text))
                location = str.strip(item.find('li', class_='item-char view-location js-location').text)
                price = str.replace(item.find('span', class_='size15').text, ' ', '').split('$')
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

                cars.append({
                    'week_number': week_num[1],
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
            page_number = page_number + 1
        else:
            break
    return cars


def get_data_from_source(page_number: int):
    """
    Parser method
    """
    r = requests.get(
        f'https://auto.ria.com/uk/search/?indexName=auto&categories.main.id=1&country.import.usa.not=-1&price.currency=1&top=2&abroad.not=0&custom.not=-1&page={page_number}&size=100'
    )

    soup = BeautifulSoup(r.content, 'html.parser')
    items = soup.body.find("div", class_='app-content').find_all("section", class_='ticket-item')

    return items


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