import pandas as pd
from dotenv import load_dotenv
import os
from src.data_receiver.weather_receiver import WeatherDataCollector


def get_and_process_weather(target_date, db_handler):
    """
    # 1. ENV
    load_dotenv()
    weather_api_key = os.environ.get("WEATHER_API_KEY")
    weather_api_key_backup = os.environ.get("WEATHER_API_KEY_BACKUP")

    # 2. WEATHER COLLECTION
    locations = db_handler.get_locations_from_database()
    collector = WeatherDataCollector(weather_api_key_backup)

    weather_data = collector.collect_and_prepare_data(target_date, target_date, locations)

    # 3. WEATHER INSERTION
    weather_region_mapping = db_handler.fetch_region_mapping()
    weather_col_mapping = {
        'region': 'location',
        'date': 'date',
        'time': 'time'
    }
    
    db_handler.insert_weather_data(weather_data, weather_region_mapping, weather_col_mapping)
    """
    # 4. WEATHER PROCESSING
    weather_data_inserted = db_handler.get_weather_data(daily_fetcher=True)

    weather_exclude = [
    'weather_id',
    'region_name',
    'icon',
    'source',
    'uvindex',
    'stations',
    'feelslike',
    'conditions',
    'description',
    'solarenergy',
    'sunsetEpoch',
    'feelslikemax',
    'feelslikemin',
    'sunriseEpoch',
    'datetimeEpoch',
    'solarradiation',
    'datetime' # wrong format, better to recreate manually
    ]
    weather_data_inserted = weather_data_inserted.drop(weather_exclude, axis=1)

    weather_data_inserted['date'] = pd.to_datetime(weather_data_inserted['date'])
    weather_data_inserted['datetime'] = pd.to_datetime(weather_data_inserted['date'].dt.date.astype(str) + ' ' + weather_data_inserted['time'])

    weather_data_inserted['precipprob_binary'] = (weather_data_inserted['precipprob'] > 0).astype(int)
    weather_data_inserted = weather_data_inserted.drop(['precipprob'], axis=1)

    weather_data_inserted['rain_bin'] = weather_data_inserted['preciptype'].apply(lambda x: int('rain' in x) if isinstance(x, list) else 0)
    weather_data_inserted['snow_bin'] = weather_data_inserted['preciptype'].apply(lambda x: int('snow' in x) if isinstance(x, list) else 0)
    weather_data_inserted['rain_snow_bin'] = weather_data_inserted['preciptype'].apply(lambda x: int('rain' in x and 'snow' in x) if isinstance(x, list) else 0)
    weather_data_inserted = weather_data_inserted.drop('preciptype', axis=1)

    # in difference from the historical dataset, where the percentage of missing visibility data reaches 60-70%,
    # in the new data it is close to 95% (and 100% for most regions) from feature importances we can understand that
    # visibility is not a critically important indicator for the model, we fill it with the median from the historical data
    weather_data_inserted['visibility'].fillna(16.22, inplace=True)

    def time_to_seconds(time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    weather_data_inserted['sunrise_seconds'] = weather_data_inserted['sunrise'].apply(time_to_seconds)
    weather_data_inserted['sunset_seconds'] = weather_data_inserted['sunset'].apply(time_to_seconds)
    weather_data_inserted['daylight_duration_seconds'] = weather_data_inserted['sunset_seconds'] - weather_data_inserted['sunrise_seconds']

    weather_data_inserted.drop(['sunrise', 'sunset'], axis=1, inplace=True)

    return weather_data_inserted

