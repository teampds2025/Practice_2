import requests
from datetime import datetime
import pandas as pd
import time


class WeatherDataCollector:
    def __init__(self, api_key,
                 base_url="https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"):
        """
        Initializes the API client.

        Args:
            api_token (str): The API token for authentication.
        """
        self.api_key = api_key
        self.base_url = base_url

    def collect_and_prepare_data(self, start_date, end_date, locations_dict):
        """
        Collects HOURLY!! weather data, enriching it with specified daily metrics,
        and prepares it directly into a list of tuples for DB insertion.

        Args:
            start_date (datetime): The starting date for collection.
            end_date (datetime): The ending date for collection.
            locations_dict (dict): Dictionary mapping location names to their coordinates.

        Returns:
             pd.DataFrame: A DataFrame.
        """
        dataset = []

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        daily_keys_to_include = {
            'tempmax', 'tempmin', 'feelslikemax', 'feelslikemin',
            'precipcover', 'sunrise', 'sunriseEpoch', 'sunset',
            'sunsetEpoch', 'moonphase',
            'conditions', 'description',
        }

        for location_name, coordinates in locations_dict.items():
            print(f"\nProcessing location: {location_name} ({coordinates})")

            query_location = coordinates
            url = f"{self.base_url}{query_location}/{start_str}/{end_str}?unitGroup=metric&include=days,hours&key={self.api_key}&contentType=json"

            try:
                print(f"Fetching data for {location_name} (from {start_str} to {end_str}...")
                response = requests.get(url)
                response.raise_for_status()  

                weather_data = response.json()

                if 'days' in weather_data:
                    for day in weather_data['days']:
                        day_date_str = day.get('datetime')  

                        daily_metrics_for_hours = {}
                        for key in daily_keys_to_include:
                            if key in day:
                                daily_metrics_for_hours[key] = day[key]

                        if 'hours' in day:
                            for hour in day['hours']:
                                hour_time_str = hour.get('datetime') 

                                hourly_data = {
                                    'location': location_name,
                                    'date': day_date_str,
                                    'time': hour_time_str,
                                }

                                for key, value in hour.items():
                                    hourly_data[key] = value
                                for daily_key, daily_value in daily_metrics_for_hours.items():
                                    hourly_data[daily_key] = daily_value

                                dataset.append(hourly_data)


                        else:
                            print(f"Warning: No 'hours' array found for {location_name} on {day_date_str}")

                else:
                    print(f"Warning: No 'days' array found for {location_name}")

                print(f"Successfully processed hourly data for {location_name}")

            except requests.exceptions.RequestException as e:
                print(f"HTTP Error collecting data for {location_name}: {e}")
            except Exception as e:
                print(f"Unexpected error processing data for {location_name}: {e}")

            time.sleep(1.5)  

        print(f"\nCollection finished. Prepared {len(dataset)} unique hourly records for database insertion.")
        dataset = pd.DataFrame(dataset)
        return dataset
