import nltk
from logger import logging_config
from . import cities_contries_continents, cities, countries, continents, SelectedFields

logger = logging_config.get_logger('geo')


def extract_continent(location):
    nes = find_places(location)

    city = None
    likely_city = False
    country = None
    likely_country = False
    continent = None
    likely_continent = False
    for n in nes:
        n = n.lower()
        if n in cities and not likely_city:
            city = n
            likely_city = True
        if n in countries and not likely_country:
            country = n
            likely_country = True
        if n in continents and not likely_continent:
            continent = n
            likely_continent = True

    if not continent:
        if country:
            for x in cities_contries_continents:
                if x[SelectedFields.country] == country:
                    continent = x[SelectedFields.continent]
        elif city:
            for x in cities_contries_continents:
                if x[SelectedFields.city] == city:
                    continent = x[SelectedFields.continent]
    if not continents:
        logger.warning('Failed to extract contient from %s' % location)
    return continent


def find_places(text):
    nes = named_entities(text)
    places = []
    for ne in nes:
        if type(ne) is nltk.tree.Tree:
            if ne.label() in ['GPE', 'PERSON', 'ORGANIZATION']:
                places.append(u' '.join([i[0] for i in ne.leaves()]))

    if not places:
        places = text
    return places


def named_entities(text):
    words = nltk.word_tokenize(text)
    pos_tag = nltk.pos_tag(words)
    nes = nltk.ne_chunk(pos_tag)
    return nes
