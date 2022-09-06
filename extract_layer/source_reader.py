"""
SOMETHING
"""
import calendar
import re
import requests
from bs4 import BeautifulSoup


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
               cars.append({
                    'week_number': week_num[1],
                    'date': today.strftime("%m-%d-%y"),
                    'day_of_week': calendar.day_name[my_date.weekday()],
                    'link': get_link(item),
                    'brand': get_brand_model_from_item(item, two_word_car_brands)['brand'],
                    'model': get_brand_model_from_item(item, two_word_car_brands)['model'],
                    'year_of_manufacture': get_year_of_manufacture(item),
                    'price_usd': get_price(item),
                    'mileage': get_mileage(item),
                    'engine_type': get_engine_type_and_volume(item, all_engine_types)['engine_type'],
                    'engine_volume': get_engine_type_and_volume(item, all_engine_types)['volume'],
                    'gearbox_type': get_gearbox_type(item),
                    'location': get_location(item)
                })
            page_number = page_number + 1
        else:
            break
    return cars


def get_data_from_source(page_number: int):
    """
    Parser method
    """
    requested_data = requests.get(
        f'https://auto.ria.com/uk/search/?indexName=auto&categories.main.id=1'
        f'&country.import.usa.not=-1&price.currency=1&top=2'
        f'&abroad.not=0&custom.not=-1&page={page_number}&size=100',
        timeout=300
    )

    soup = BeautifulSoup(requested_data.content, 'html.parser')
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


def get_mileage(item) -> int:
    """
    Something will be written here later...
    """
    mileage = re.findall('[0-9]+', str.lstrip(item.find('li', class_='item-char js-race').text))
    mileage = int(mileage[0]) * 1000

    return mileage


def get_year_of_manufacture(item) -> int:
    """
    Something will be written here later...
    """
    year = str.strip(item.find('a', class_='address').text)
    year = int(year[-4:])

    return year


def get_location(item) -> str:
    """
    Something will be written here later...
    """
    location = str.strip(item.find('li', class_='item-char view-location js-location').text)
    location = location[:-8]

    return location


def get_price(item) -> int:
    """
    Something will be written here later...
    """
    price = str.replace(item.find('span', class_='size15').text, ' ', '').split('$')
    price = int(price[0])

    return price


def get_engine_type_and_volume(item, all_engine_types) -> dict:
    """
    Something will be written here later...
    """
    unstyle_characteristic = re.split(r'\s{3,}', str.strip(item.find('ul', class_="unstyle characteristic").text))
    egine_type_and_volume = unstyle_characteristic[2].split(', ')
    if len(egine_type_and_volume) < 2:
        if egine_type_and_volume[0] in all_engine_types.keys():
            output_data = {'engine_type': egine_type_and_volume[0], 'volume': 0.0}
        else:
            volume = egine_type_and_volume[:2]
            volume = volume[-1].split()
            output_data = {'engine_type': 'Not specified', 'volume': float(volume[0])}
    else:
        volume = egine_type_and_volume[1].split()
        output_data = {'engine_type': egine_type_and_volume[0], 'volume': float(volume[0])}

    return output_data


def get_gearbox_type(item):
    """
    Something will be written here later...
    """
    gearbox_type = re.split(r'\s{3,}', str.strip(item.find('ul', class_="unstyle characteristic").text))

    return gearbox_type[-1]


def get_link(item) -> str:
    """
    Something will be written here later...
    """
    return item.find('a', class_='m-link-ticket').get('href')

