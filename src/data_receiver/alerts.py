import pandas as pd
from alerts_in_ua import Client as AlertsClient


class AlertsAPIHandler:
    """
    Handles fetching alert data from the alerts API.
    """

    def __init__(self, api_token):
        """
        Initializes the API client.

        Args:
            api_token (str): The API token for authentication.
        """
        if not api_token:
            raise ValueError("API token cannot be empty.")
        try:
            self.client = AlertsClient(token=api_token)
            print("AlertsClient initialized successfully.")
        except Exception as e:
            print(f"Error initializing AlertsClient: {e}")

    def fetch_active_alerts_df(self):
        """
        Fetches active alerts from the API and returns them as a Pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing active alerts,
                          or an empty DataFrame if an error occurs or no alerts are active.
        """

        try:
            active_alerts = self.client.get_active_alerts()

            if not active_alerts:
                print("No active alerts found.")
                return pd.DataFrame()

            keys = ['id', 'location_title', 'location_type', 'started_at', 'finished_at', 'updated_at', 'alert_type',
                    'location_uid', 'location_oblast', 'location_raion', 'notes', 'calculated'] # all that we can 
            list_of_dictionaries = [
                {key: getattr(alert, key, None) for key in keys}
                for alert in active_alerts
            ]

            df = pd.DataFrame(list_of_dictionaries)
            print(f"Successfully fetched {len(df)} active alerts.")

            return df

        except Exception as e:
            print(f"Error fetching or processing active alerts: {e}")
            return pd.DataFrame()
