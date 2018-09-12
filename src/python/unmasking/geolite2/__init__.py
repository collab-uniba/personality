__all__ = ['cities_contries_continents', 'SelectedFields', 'cities', 'continents', 'countries']


from csv import DictReader
from enum import Enum

import unidecode
import os


class SelectedFields(Enum):
    continent = 'continent_name'
    country = 'country_name'
    city = 'city_name'


with open(os.path.join('.', 'geolite2', 'GeoLite2-City-Locations-en.csv')) as f:
    reader = DictReader(f)
    cities_contries_continents = [r for r in reader]
    cities = list(sorted(set(unidecode.unidecode(elem['city_name']).lower() for elem in cities_contries_continents)))
    countries = list(
        sorted(set(unidecode.unidecode(elem['country_name']).lower() for elem in cities_contries_continents)))
    continents = list(
        sorted(set(unidecode.unidecode(elem['continent_name']).lower() for elem in cities_contries_continents)))
    cities_contries_continents = [{SelectedFields.city: unidecode.unidecode(elem['city_name']).lower(),
                                   SelectedFields.country: unidecode.unidecode(elem['country_name']).lower(),
                                   SelectedFields.continent: unidecode.unidecode(elem['continent_name']).lower()} for
                                  elem in cities_contries_continents]
