import json
import os

from datetime import datetime

import cactus
import dotenv
import pandas
import pytz
import requests
import twitter

# Load the .env
dotenv.load_dotenv(dotenv.find_dotenv())

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
    # url = 'https://cofgisonline.maps.arcgis.com/sharing/rest/content/items/664add6af8a9465b8842b24ec2c492e4/data?f=json'
    # data = fetch_json(url)
    # return int(data['widgets'][3]['datasets'][1]['data'])

    # return 793501 # Population aged 16+
    return 1042157 # Total population


def get_vaccinated_FCDPH():
    url = 'https://services3.arcgis.com/ibgDyuD2DLBge82s/arcgis/rest/services/COVID19_Immunization_Unique_View/FeatureServer/0/query?f=json&where=(recip_county_desc%3D%27Fresno%27%20AND%20vax_series_complete%3D%27YES%27%20OR%20recip_county_desc%20IS%20NULL%20AND%20vax_series_complete%3D%27YES%27)&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22count%22%2C%22onStatisticField%22%3A%22OBJECTID%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&resultType=standard&cacheHint=true'
    data = fetch_json(url)
    return int(data['features'][0]['attributes']['value'])


def get_vaccinated_CADPH():
    url = 'https://data.chhs.ca.gov/dataset/e283ee5a-cf18-4f20-a92c-ee94a2866ccd/resource/130d7ba2-b6eb-438d-a412-741bde207e1c/download/covid19vaccinesbycounty.csv'
    df = pandas.read_csv(url)
    return int(df[df['county'] == 'Fresno'].iloc[-1]['cumulative_fully_vaccinated'])


def get_seven_day_average_increase(df):
    df = df.iloc[len(df) - 7:]
    vaccinated_average = df['fully_vaccinated'].mean()
    vaccinated_percent = (100. / get_population()) * vaccinated_average

    one_dose_average = df['partially_vaccinated'].mean()
    one_dose_percent = (100. / get_population()) * one_dose_average

    return {
        'seven_day_vaccinated': int(round(vaccinated_average)),
        'seven_day_vaccinated_percent': vaccinated_percent,
        'seven_day_one_dose': int(round(one_dose_average)),
        'seven_day_one_dose_percent': one_dose_percent,
    }


def fetch_current_stats():
    url = 'https://data.chhs.ca.gov/dataset/e283ee5a-cf18-4f20-a92c-ee94a2866ccd/resource/130d7ba2-b6eb-438d-a412-741bde207e1c/download/covid19vaccinesbycounty.csv'
    df = pandas.read_csv(url)
    df = df[df['county'] == 'Fresno']
    df = df.iloc[len(df) - 60:]

    stats = {
        'population': get_population(),
        'vaccinated': int(df.iloc[-1]['cumulative_fully_vaccinated']),
        'one_dose': int(df.iloc[-1]['cumulative_at_least_one_dose']),
    }

    stats.update(
        vaccinated_percent=(100. / stats['population']) * stats['vaccinated'],
        one_dose_percent=(100. / stats['population']) * stats['one_dose'],
    )

    stats.update(get_seven_day_average_increase(df))

    stats['historical'] = {
        'dates': df['administered_date'].to_list(),
        'fully_vaccinated': df['fully_vaccinated'].to_list(),
        'cumulative_fully_vaccinated': df['cumulative_fully_vaccinated'].to_list(),
        'percents': [round((100. / stats['population']) * x, 1) for x in df['cumulative_fully_vaccinated'].to_list()]
    }
    return stats


def progress_bar(percent):
    bar_filled = '▓'
    bar_empty = '░'
    length = 15

    progress_bar = bar_filled * int((percent / (100. / length)))
    progress_bar += bar_empty * (length - len(progress_bar))
    return f'{progress_bar} {percent:.1f}%'


def send_tweet(population, vaccinated, vaccinated_percent, *args, **kwargs):
    message = '\n'.join([
        '‼️ Fresno Vaccination Progress:',
        '',
        progress_bar(vaccinated_percent),
        '',
        'Learn more at FresnoVax.com'
    ])

    api = twitter.Api(
        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
        access_token_key=os.environ['TWITTER_ACCESS_KEY'],
        access_token_secret=os.environ['TWITTER_ACCESS_SECRET']
    )

    if api.VerifyCredentials() is not None:
        api.PostUpdate(message)


def main():
    previous = load_stats()
    previous.pop('updated', None)
    current = fetch_current_stats()

    if previous != current:
        save_stats(current)
        os.system('cactus build')
        send_tweet(**current)


if __name__ == '__main__':
    main()
