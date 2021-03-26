import json
import os

from datetime import datetime

import cactus
import pytz
import requests

STATS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../vaccine-stats.json'))

def current_timestamp():
    return (pytz.utc
        .localize(datetime.utcnow())
        .astimezone(pytz.timezone('America/Los_Angeles'))
        .isoformat()
    )

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}

    with open(STATS_FILE, 'r') as f:
        return json.loads(f.read())


def save_stats(stats):
    stats['updated'] = current_timestamp()
    with open(STATS_FILE, 'w') as f:
        f.write(json.dumps(stats))


def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_population():
    url = 'https://cofgisonline.maps.arcgis.com/sharing/rest/content/items/664add6af8a9465b8842b24ec2c492e4/data?f=json'
    data = fetch_json(url)
    return int(data['widgets'][3]['datasets'][1]['data'])


def get_vaccinated():
    url = 'https://services3.arcgis.com/ibgDyuD2DLBge82s/arcgis/rest/services/COVID19_Immunization_Unique_View/FeatureServer/0/query?f=json&where=(recip_county_desc%3D%27Fresno%27%20AND%20vax_series_complete%3D%27YES%27%20OR%20recip_county_desc%20IS%20NULL%20AND%20vax_series_complete%3D%27YES%27)&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22count%22%2C%22onStatisticField%22%3A%22OBJECTID%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&resultType=standard&cacheHint=true'
    data = fetch_json(url)
    return int(data['features'][0]['attributes']['value'])


def fetch_current_stats():
    stats = {
        'population': get_population(),
        'vaccinated': get_vaccinated(),
    }
    stats['percentage'] = (100. / stats['population']) * stats['vaccinated']
    return stats


def main():
    previous = load_stats()
    previous.pop('updated', None)
    current = fetch_current_stats()

    if previous != current:
        save_stats(current)


if __name__ == '__main__':
    main()
