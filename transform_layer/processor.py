"""
Something will be written here later...
"""


class Processor:
    """
    Something will be written here later...
    """

    def translate_engine_type(self, cars: list, all_engine_types: dict) -> list:
        """
        this method replaces cyrillic engine fuel type to English
        """
        for car in cars:
            for key, value in car.items():
                if key == 'engine_type' and value in all_engine_types.keys():
                    value = all_engine_types[value]
                    car.update({key: value})

        return cars

    def translate_gearbox_type(self, cars: list, all_gearbox_types: dict) -> list:
        """
        this method replaces cyrillic gearbox type to English
        """
        for car in cars:
            for key, value in car.items():
                if key == 'gearbox_type' and value in all_gearbox_types.keys():
                    value = all_gearbox_types[value]
                    car.update({key: value})

        return cars
