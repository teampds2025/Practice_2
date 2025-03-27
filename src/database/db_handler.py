import mysql.connector
from mysql.connector import Error
import pandas as pd
import datetime
import json


class DatabaseHandler:
    """
    A class to handle database operations for the war events prediction system.
    """

    def __init__(self, host, database, user, password, port=3306):
        """
        Initialize database connection parameters.

        Args:
            host (str): The database host address
            database (str): The database name
            user (str): The database username
            password (str): The database password
            port (int, optional): The database port. Defaults to 3306.
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None

    def connect(self):
        """
        Establish a connection to the database.
        """

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )

        except Error as e:
            print(f"Error connecting to MySQL database: {e}")

    def disconnect(self):
        """
        Close the database connection.
        """

        if self.connection and self.connection.is_connected():
            self.connection.close()

    def debug(self, test):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(test)
            for row in cursor.fetchall():
                print(row)
            cursor.close()

        except Error as e:
            print(f"Error: {e}")
            return None

    def create_tables(self):
        """
        Create necessary tables if they don't exist.
        """

        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    region_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_name VARCHAR(100) UNIQUE NOT NULL,
                    latitude FLOAT,
                    longitude FLOAT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather (
                    weather_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_id INT NOT NULL,
                    date DATE NOT NULL,
                    time TIME NULL,          -- Store time (NULL for daily summary)
                    data JSON NOT NULL,      -- Store the detailed weather metrics
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_weather_observation (region_id, date, time)
                ) 
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS isw_reports (
                    report_id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    content TEXT,
                    url VARCHAR(255)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alarm_event_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_id INT NOT NULL,
                    start_datetime_utc DATETIME NOT NULL,
                    end_datetime_utc DATETIME NULL,
                    event_type VARCHAR(50),
                    raw_data JSON NULL,
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
                )
            """)

            self.connection.commit()
            cursor.close()

        except Error as e:
            print(f"Error creating tables: {e}")

    def initialize_regions_in_database(self):
        regions_data = [
            ("Kyiv City", 50.4501, 30.5234),
            ("Kyiv", 50.4501, 30.5234),
            ("Vinnytsia", 49.2328, 28.4815),
            ("Lutsk", 50.7472, 25.3254),
            ("Dnipro", 48.4647, 35.0462),
            ("Donetsk", 48.0159, 37.8028),
            ("Zhytomyr", 50.2547, 28.6587),
            ("Uzhhorod", 48.6208, 22.2879),
            ("Zaporizhzhia", 47.8388, 35.1396),
            ("Ivano-Frankivsk", 48.9226, 24.7111),
            ("Kropyvnytskyi", 48.5079, 32.2623),
            ("Luhansk", 48.5742, 39.3075),
            ("Lviv", 49.8397, 24.0297),
            ("Mykolaiv", 46.9750, 31.9946),
            ("Odesa", 46.4825, 30.7233),
            ("Poltava", 49.5883, 34.5514),
            ("Rivne", 50.6199, 26.2516),
            ("Sumy", 50.9077, 34.7981),
            ("Ternopil", 49.5535, 25.5948),
            ("Kharkiv", 49.9935, 36.2304),
            ("Kherson", 46.6354, 32.6169),
            ("Khmelnytskyi", 49.4229, 26.9871),
            ("Cherkasy", 49.4444, 32.0598),
            ("Chernivtsi", 48.2921, 25.9358),
            ("Chernihiv", 51.4982, 31.2893)
        ]

        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()

            for region_name, latitude, longitude in regions_data:
                cursor.execute("""
                    INSERT INTO regions (region_name, latitude, longitude)
                    VALUES (%s, %s, %s)
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude)
                """, (region_name, latitude, longitude))

            self.connection.commit()
            cursor.close()
            print(f"Successfully initialized {len(regions_data)} regions in the database")

        except Exception as e:
            print(f"Error initializing regions: {e}")

    def get_locations_from_database(self):
        """
        Retrieves locations from the database and formats them as a dictionary.

        Returns:
            dict: Dictionary mapping regions to their coordinates
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            query = """
                SELECT region_name, latitude, longitude 
                FROM regions
            """

            locations_df = pd.read_sql(query, self.connection)
            locations_dict = {}
            for _, row in locations_df.iterrows():
                coordinates = f"{row['latitude']},{row['longitude']}"
                locations_dict[row['region_name']] = coordinates

            return locations_dict

        except Exception as e:
            print(f"Error retrieving locations from database: {e}")

    def fetch_region_mapping(self):
        """
        Fetches the region_id to region_name mapping from the database.

        Returns:
            dict: Dictionary mapping regions to their keys
        """

        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT region_id, region_name FROM regions")
            regions_db = cursor.fetchall()
            cursor.close()
            region_mapping = {region['region_name']: region['region_id'] for region in regions_db}
            print(f"Region mapping fetched successfully ({len(region_mapping)} regions).")
            return region_mapping

        except Error as e:
            print(f"Database Error fetching region mapping: {e}")
            return None

        except Exception as e:
            print(f"An unexpected error occurred fetching region mapping: {e}")
            return None

    def insert_isw_report(self, df):
        """
        Insert multiple ISW reports from a DataFrame.

        Args:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            records = []

            for _, row in df.iterrows():
                date_val = row['date']
                if isinstance(date_val, str):
                    date_val = datetime.datetime.strptime(date_val, '%Y-%m-%d').date()
                elif isinstance(date_val, datetime.datetime):
                    date_val = date_val.date()

                content = row['report_text']
                url = row['url']
                records.append((date_val, content, url))

            cursor = self.connection.cursor()
            query = """
                INSERT INTO isw_reports (date, content, url)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    url = VALUES(url)
            """
            cursor.executemany(query, records)
            self.connection.commit()
            cursor.close()

        except Error as e:
            print(f"Error inserting ISW reports: {e}")

    def get_isw_reports(self):
        """
        Retrieve ISW reports from the database.

        Returns:
            pandas.DataFrame: DataFrame containing the ISW reports
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            query = """
                SELECT date, content, url
                FROM isw_reports
                WHERE 1=1
            """

            return pd.read_sql(query, self.connection)

        except Error as e:
            print(f"Error retrieving ISW reports: {e}")
            return pd.DataFrame()

    def get_weather_data(self, expand_json=True):
        """
        Retrieves weather data from the database, optionally expanding the JSON data column.

        Args:
            expand_json (bool, optional): If True, parses the 'data' JSON column and expands it into separate columns.
            If False, returns the raw JSON string. Defaults to True.

        Returns:
            pandas.DataFrame: A DataFrame containing the weather data
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            sql_query = """
                            SELECT
                                w.weather_id, w.region_id, r.region_name, 
                                w.date, w.time, w.data  
                            FROM weather w
                            JOIN regions r ON w.region_id = r.region_id
                            ORDER BY r.region_name, w.date, w.time;
                        """

            print(f"Executing query to fetch weather data...")
            df = pd.read_sql(sql_query, self.connection, parse_dates=['date'])

            if df.empty:
                print("No weather data found.")
                return df

            print(f"Retrieved {len(df)} weather records.")

            if expand_json and 'data' in df.columns:
                json_records = []

                for index, json_str in df['data'].items():
                    parsed_data = json.loads(json_str)
                    json_records.append(parsed_data)
                expanded_data = pd.json_normalize(json_records)
                expanded_data.index = df.index

                df_expanded = pd.concat([df.drop(columns=['data']), expanded_data], axis=1)
                df_expanded['time'] = df_expanded['time'].apply(lambda x: str(x).split()[-1] if pd.notna(x) else None) # !!!!
                print("JSON data expanded successfully.")

                return df_expanded

            else:
                df['time'] = df['time'].apply(lambda x: str(x).split()[-1] if pd.notna(x) else None)
                return df

        except Error as e:
            print(f"Database error retrieving weather data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred while retrieving weather data: {e}")
            return pd.DataFrame()

    def prepare_weather_data(self, df, region_mapping, col_mapping):
        """
        Prepares JSON data for insertion into a MySQL table.

        Parameters:
            df (pd.DataFrame): The input DataFrame.
            region_mapping (dict): A mapping to translate location values into region IDs.
            col_mapping (dict): A mapping of standard field names to the actual DataFrame column names.
                Expected keys include:
                  - 'region': column name for the region location.
                  - 'date': column name for the date value.
                  - 'time': column name for the time value.

        Returns:
            list: A list of dictionaries containing:
                - 'region_id': the mapped region id,
                - 'date_value': the date value,
                - 'time_value': the time value,
                - 'json_data': the remaining data as a JSON string.
        """
        df = df.replace({float('nan'): None})  # !!!!!!!
        output = []

        for _, row in df.iterrows():
            region_value = row[col_mapping['region']]
            region_id = region_mapping.get(region_value)
            if region_id is None:
                print(f"Skipping unknown location: {region_value}")
                continue

            date_value = row[col_mapping['date']]
            time_value = row[col_mapping['time']]

            json_data_dict = row.to_dict()
            for key in col_mapping.values():
                json_data_dict.pop(key, None)
            json_data = json.dumps(json_data_dict, default=str)

            output.append((region_id, date_value, time_value, json_data))

        return output

    def prepare_alerts_data(self, df, region_mapping, col_mapping):
        """
        Prepares JSON data for insertion into a MySQL table.

        Parameters:
            df (pd.DataFrame): The input DataFrame.
            region_mapping (dict): A mapping to translate location values into region IDs.
            col_mapping (dict): A mapping of standard field names to the actual DataFrame column names.
                Expected keys include:
                  - 'region': column name for the region location.
                  - 'start_date': column name for the start date value.
                  - 'end_date': column name for the end date value.
                  - 'type': column name for the type value.

        Returns:
            list: A list of dictionaries containing:
                - 'region_id': the mapped region id,
                - 'start_datetime_utc': the date value,
                - 'end_datetime_utc': the date value,
                - 'event_type': the type value,
                - 'raw_data': the remaining data as a JSON string.
        """
        df = df.replace({float('nan'): None})  # !!!!!!!
        output = []

        for _, row in df.iterrows():
            region_value = row[col_mapping['region']]
            region_id = region_mapping.get(region_value)
            if region_id is None:
                print(f"Skipping unknown location: {region_value}")
                continue

            start_datetime_utc = row[col_mapping['start_date']]
            end_datetime_utc = row[col_mapping['end_date']]
            event_type = row[col_mapping['type']]

            json_data_dict = row.to_dict()
            for key in col_mapping.values():
                json_data_dict.pop(key, None)
            raw_data = json.dumps(json_data_dict, default=str)

            output.append((region_id, start_datetime_utc, end_datetime_utc, event_type, raw_data))

        return output

    def insert_weather_data(self, df, region_mapping, col_mapping):
        """
        Inserts weather data into the `weather` table after preparing it.

        Args:
            df (pandas.DataFrame): DataFrame containing the raw weather data.
            region_mapping (dict): Dictionary mapping region names to region IDs.
            col_mapping (dict): Dictionary mapping standard field names ('region', 'date', 'time')
                                to actual column names in the DataFrame.
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()

        cursor = self.connection.cursor()

        insert_sql = """
            INSERT INTO weather (region_id, date, time, data)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE data = VALUES(data)
        """

        prepared = self.prepare_weather_data(df, region_mapping, col_mapping)
        cursor.executemany(insert_sql, prepared)
        self.connection.commit()
        print(f"Successfully inserted/handled {cursor.rowcount} weather records.")
        cursor.close()

    def insert_alerts_data(self, df, region_mapping, col_mapping):
        """
        Inserts alerts data into the `alerts` table after preparing it.
            
        Args:
            df (pandas.DataFrame): DataFrame containing the raw alerts data.
            region_mapping (dict): Dictionary mapping region names to region IDs.
            col_mapping (dict): Dictionary mapping standard field names ('region', 'start_date',
                                'end_date', 'type') to actual column names in the DataFrame.
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()

        cursor = self.connection.cursor()

        insert_sql = """
            INSERT INTO alerts (region_id, start_datetime_utc, end_datetime_utc, event_type, raw_data)
                VALUES (%s, %s, %s, %s, %s)
        """

        prepared = self.prepare_alerts_data(df, region_mapping, col_mapping)
        cursor.executemany(insert_sql, prepared)
        self.connection.commit()
        print(f"Successfully inserted/handled {cursor.rowcount} weather records.")
        cursor.close()

    def get_alerts(self):
        """
        Retrieves alert data from the database

        Returns:
            pandas.DataFrame
        """

        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    print("Failed to connect to the database.")
                    return pd.DataFrame()

            sql_query = """
                            SELECT 
                                a.alarm_event_id, 
                                a.region_id, 
                                r.region_name, 
                                a.start_datetime_utc, 
                                a.end_datetime_utc, 
                                a.event_type, 
                                a.raw_data
                            FROM alerts a
                            JOIN regions r ON a.region_id = r.region_id
                            ORDER BY a.start_datetime_utc DESC;
                        """

            df = pd.read_sql(
                sql_query,
                self.connection,
                parse_dates=['start_datetime_utc', 'end_datetime_utc']
            )

            if df.empty:
                print("No alert data found matching the criteria.")
            else:
                print(f"Retrieved {len(df)} alert records.")

            return df

        except Error as e:
            print(f"Database error retrieving alerts: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred while retrieving alerts: {e}")
            return pd.DataFrame()
