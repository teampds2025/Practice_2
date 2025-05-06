import requests
import pandas as pd
from datetime import datetime


class UkraineAlarmAPIClient:
    """
    Client to interact with the Ukraine Alarm API.
    Provides methods to fetch alerts by region and by date history.
    """
    def __init__(self, api_key, base_url = "https://api.ukrainealarm.com/api/v3"):
        """
        Initialize the client with the given API key and base URL.
        """
        
        self.headers = {
            "Authorization": api_key
        }
        self.base_url = base_url

    def get_regions(self):
        """
        Fetch alert regions data from the API.
        """
        
        url = f"{self.base_url}/alerts/regions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)

    def get_date_history(self, date_value):
        """
        Fetch alarm history for a specific date.
        """
        
        if isinstance(date_value, datetime):
            date_str = date_value.strftime('%Y%m%d')
        elif isinstance(date_value, str):
            cleaned = date_value.replace('-', '')
            if len(cleaned) != 8 or not cleaned.isdigit():
                raise ValueError("date_value string must be in 'YYYYMMDD' or 'YYYY-MM-DD' format")
            date_str = cleaned
        else:
            raise ValueError("date_value must be a datetime or string in 'YYYYMMDD' format")

        url = f"{self.base_url}/alerts/dateHistory?date={date_str}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
