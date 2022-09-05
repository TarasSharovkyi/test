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
            for k, v in car.items():
                if k == 'engine_type' and v in all_engine_types.keys():
                    v = all_engine_types[v]
                    car.update({k: v})

        return cars

    def translate_gearbox_type(self, cars: list, all_gearbox_types: dict) -> list:
        """
        this method replaces cyrillic gearbox type to English
        """
        for car in cars:
            for k, v in car.items():
                if k == 'gearbox_type' and v in all_gearbox_types.keys():
                    v = all_gearbox_types[v]
                    car.update({k: v})

        return cars
