import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
from src.database.db_handler import DatabaseHandler
from src.data_receiver.isw import ISWDataCollector
from src.data_receiver.data import WeatherDataCollector
from src.data_receiver.alerts import AlertsAPIHandler

"""
The API used for alarms allows you to get information either 
about alarms that are currently occurring in all areas, 
or information about all alarms for the last month in a particular area.

Unlike IWS reports and weather information, which we both use for daily 
predictions and collect for model fine-tuning in the future, we only 
collect alarm information for fine-tuning and do not use it for daily predictions.

With this in mind, the logical solution for alarm data is to collect the past
 month once a month for all alarms and all areas. The code for this will be created later.
"""

db = DatabaseHandler(
    host="",
    database="",
    user="",
    password="",
    port=3306
)
db.connect()


today_str = datetime.now().strftime('%Y-%m-%d')
start_date = datetime.strptime(today_str, '%Y-%m-%d')
end_date = datetime.strptime(today_str, '%Y-%m-%d')
yesterday = datetime.now() - timedelta(days=1)
yesterday_date = datetime(yesterday.year, yesterday.month, yesterday.day)

locations = db.get_locations_from_database()
collector = WeatherDataCollector("")
weather_data = collector.collect_and_prepare_data(start_date, end_date, locations)
weather_region_mapping = db.fetch_region_mapping()
weather_col_mapping = {
    'region': 'location',
    'date': 'date',
    'time': 'time'
}
db.insert_weather_data(weather_data, weather_region_mapping, weather_col_mapping)


isw_collector = ISWDataCollector()
isw_data = isw_collector.collect_data(yesterday_date, yesterday_date)
db.insert_isw_report(isw_data)



