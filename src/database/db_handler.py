import mysql.connector
from mysql.connector import Error
import pandas as pd
import datetime
import json


class DatabaseHandler:
    """
    A class to handle database operations, particularly for data related to regions,
    weather, reports, alarms, predictions, and models.
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
                    time TIME NULL,         
                    data JSON NOT NULL,      
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_weather_observation (region_id, date, time)
                ) 
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS isw_reports (
                    isw_report_id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    content TEXT,
                    url VARCHAR(255)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_reports (
                    tg_report_id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL, 
                    content TEXT
                )
            """) 

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alarms (
                    alarm_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_id INT NOT NULL,
                    start DATETIME NOT NULL,
                    end DATETIME NOT NULL,
                    data JSON NULL,
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_alarm_observation (region_id, start)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merged_data (
                    report_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_id INT NOT NULL,
                    date DATE NOT NULL,
                    time TIME NULL,  
                    data JSON NULL,
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_daily_set (region_id, date, time)
                    
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_id INT NOT NULL,
                    date DATE NOT NULL,
                    time TIME NULL,
                    prediction_value TINYINT(1),
                    raw_probabilities DECIMAL(9, 8),
                    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_prediction_set (region_id, date, time)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions  (
                    model_id INT AUTO_INCREMENT PRIMARY KEY,
                    model_name VARCHAR(100),
                    model_version VARCHAR(20) UNIQUE,
                    last_trained_on DATE,
                    model_blob LONGBLOB,
                    scaler_blob LONGBLOB
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    metric_id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    model_version VARCHAR(20),
                    accuracy DECIMAL(6,4),
                    precision_val DECIMAL(6,4),
                    recall DECIMAL(6,4),
                    f1_score DECIMAL(6,4),
                    roc_auc DECIMAL(6,4),
                    conf_matrix JSON,
                    FOREIGN KEY (model_version) REFERENCES model_versions(model_version) ON DELETE CASCADE,
                    UNIQUE KEY unique_metrics_set (model_version, date)
                )
            """)


            self.connection.commit()
            cursor.close()

        except Error as e:
            print(f"Error creating tables: {e}")
            
    def initialize_regions_in_database(self):
        """
        Populates the 'regions' table with a predefined list of Ukrainian regions
        and their coordinates. Skips insertion if a region already exists.
        """
        
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
                    INSERT IGNORE INTO regions (region_name, latitude, longitude)
                    VALUES (%s, %s, %s)
                """, (region_name, latitude, longitude))

            self.connection.commit()
            cursor.close()
            print(f"Successfully initialized {len(regions_data)} regions in the database")

        except Error as e:
             print(f"Database error during region initialization: {e}")
        except Exception as e:
            print(f"Unexpected error during region initialization: {e}")

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

        except Error as e:
             print(f"Database error retrieving locations: {e}")
             return {}
        except Exception as e:
            print(f"An unexpected error during retrieving locations: {e}")
            return {}

    
    def fetch_region_mapping(self):
        """
        Fetches the region_id to region_name mapping from the database.
    
        Returns:
            dict: Dictionary mapping region_name to region_id, sorted by region_id
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
    
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT region_id, region_name FROM regions")
            regions_db = cursor.fetchall()
            cursor.close()
    
            sorted_regions = sorted(regions_db, key=lambda x: x['region_id'])
    
            region_mapping = {region['region_name']: region['region_id'] for region in sorted_regions}
            print(f"Region mapping fetched successfully ({len(region_mapping)} regions).")
            return region_mapping
    
        except Error as e:
            print(f"Database Error fetching region mapping: {e}")
            return {}
    
        except Exception as e:
            print(f"An unexpected error during fetching region mapping: {e}")
            return {}


    def insert_isw_report(self, df):
        """
        Insert or update ISW reports from a DataFrame into the 'isw_reports' table.
        Uses date as the key for updating existing reports.

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
            print(f"Successfully inserted/handled {cursor.rowcount} isw reports.")
            cursor.close()

        except Error as e:
            print(f"Database error inserting ISW reports: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting ISW reports: {e}")


    def insert_model(self, model_name, version, last_trained_on, model_blob, scaler_blob):
        """
        Insert model metadata and blobs into the 'model_versions' table.
        Ignores insertion if a model with the same version already exists.

        Args:
            model_name (str): Name of the model.
            version (str): Unique version identifier for the model.
            last_trained_on (date): Date when the model was last trained.
            model_blob (bytes): Binary data of the serialized model.
            scaler_blob (bytes): Binary data of the serialized scaler.
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute("""
            INSERT IGNORE INTO model_versions (model_name, model_version, last_trained_on, model_blob, scaler_blob)
            VALUES (%s, %s, %s, %s, %s)
            """, (model_name, version, last_trained_on, model_blob, scaler_blob))
            self.connection.commit()
            print(f"Successfully inserted/handled model insertion")
            cursor.close()

        except Error as e:
            print(f"Database error inserting model version {version}: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting model version {version}: {e}")

    def get_model_by_version(self, model_version):
        """
        Retrieve model_blob and scaler_blob for a given model version.

        Args:
            model_version (str): The version of the model to retrieve.

        Returns:
            tuple: (model_blob, scaler_blob) if found, otherwise (None, None).
        """
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
    
            sql_query = """
                SELECT model_blob, scaler_blob 
                FROM model_versions 
                WHERE model_version = %s
            """
    
            cursor = self.connection.cursor()
            cursor.execute(sql_query, (model_version,))
            result = cursor.fetchone()
            cursor.close()
    
            if result:
                return result[0], result[1]  # model_blob, scaler_blob
            else:
                return None, None
    
        except Error as e:
            print(f"Database error retrieving model version {model_version}: {e}")
            return None, None
        except Exception as e:
             print(f"An unexpected error occurred retrieving model version {model_version}: {e}")
             return None, None

    def get_model_info(self):
        """
        Retrieve metadata for all models stored in the 'model_versions' table.

        Returns:
            df (pandas.DataFrame)
        """
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            sql_query = """
                SELECT model_name, model_version, last_trained_on, model_blob, scaler_blob FROM model_versions
            """

            df = pd.read_sql(
                sql_query,
                self.connection,
                parse_dates=['last_trained_on']
            )
            
            return df

        except Error as e:
            print(f"Database error retrieving model info: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred retrieving model info: {e}")
            return pd.DataFrame()

    def insert_metrics(self, date, model_version, accuracy, precision, recall, f1_score, roc_auc, conf_matrix):
        """
        Insert model performance metrics for a specific date and model version
        into the 'daily_metrics' table. Ignores insertion if metrics for the
        same date and model version already exist.

        Args:
            date (date): The date for which the metrics apply.
            model_version (str): The version of the model used.
            accuracy (float): Accuracy score.
            precision (float): Precision score.
            recall (float): Recall score.
            f1_score (float): F1 score.
            roc_auc (float): ROC AUC score.
            conf_matrix (str): Confusion matrix, stored as a JSON string.
        """
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute("""
            INSERT IGNORE INTO daily_metrics (date, model_version, accuracy, precision_val, recall, f1_score, roc_auc, conf_matrix)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (date, model_version, accuracy, precision, recall, f1_score, roc_auc, conf_matrix))
            self.connection.commit()
            print(f"Successfully inserted/handled {cursor.rowcount} metrics records")
            cursor.close()

        except Error as e:
            print(f"Database error inserting metrics for {model_version} on {date}: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting metrics for {model_version} on {date}: {e}")

    def get_metrics(self, daily_fetcher=False):
        """
        Retrieves model performance metrics from the 'daily_metrics' table, joined with
        model names from 'model_versions'.

        Args:
            daily_fetcher (bool): If True, retrieves metrics only for the latest available date.
                                  If False (default), retrieves all metrics.

        Returns:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            base_query = """
                            SELECT 
                                d.date, 
                                m.model_name, 
                                d.model_version,
                                d.accuracy,
                                d.precision_val,
                                d.recall,
                                d.f1_score,
                                d.roc_auc,
                                d.conf_matrix
                            FROM daily_metrics d
                            JOIN model_versions m ON d.model_version = m.model_version
                        """

            where_clause = ""
            if daily_fetcher:
                # Check if the table is empty first to avoid errors with MAX() on empty table
                cursor = self.connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM daily_metrics")
                count = cursor.fetchone()[0]
                cursor.close()
                if count > 0:
                    where_clause = "WHERE d.date = (SELECT MAX(date) FROM daily_metrics)"
                    print("Filtering metrics data for the last available date.")
                else:
                    print("No metrics data found, cannot filter for last day.")
                    return pd.DataFrame()

            sql_query = f"{base_query} {where_clause}"

            df = pd.read_sql(
                sql_query,
                self.connection,
                parse_dates=['date']
            )

            if df.empty:
                print("No data found.")
            else:
                print(f"Retrieved {len(df)} alert records.")

            return df

        except Error as e:
            print(f"Database error retrieving metrics: {e}")
            return pd.DataFrame()
        except Exception as e:
             print(f"An unexpected error occurred retrieving metrics: {e}")
             return pd.DataFrame()


    
    def insert_predictions(self, df):
        """
        Insert prediction results from a DataFrame into the 'predictions' table.
        Ignores insertion if a prediction for the same region, date, and time already exists.

        Args:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            records = []

            for _, row in df.iterrows():
                reg_id_val = row['region_id']
                date_val = row['date']
                time_val = row['time']
                pred_val = row['is_alarm_active']
                proba_val = row['raw_probabilities']
                records.append((reg_id_val, date_val, time_val, pred_val, proba_val))

            cursor = self.connection.cursor()
            query = """
                INSERT IGNORE INTO predictions (region_id, date, time, prediction_value, raw_probabilities)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.executemany(query, records)
            self.connection.commit()
            print(f"Successfully inserted/handled {cursor.rowcount} predictions records. Sanity check for daily runner: expected value is 576/0")
            cursor.close()

        except Error as e:
            print(f"Database error inserting predictions: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting predictions: {e}")


    def get_predictions(self, daily_fetcher=False):
        """
        Retrieves prediction data from the 'predictions' table, joined with region names.

        Args:
            daily_fetcher (bool): If True, retrieves predictions only for the latest available date.
                                  If False (default), retrieves all predictions.

        Returns:
            df (pandas.DataFrame)
        """

        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            base_query = """
                            SELECT 
                                p.region_id, 
                                r.region_name, 
                                p.date, 
                                p.time, 
                                p.prediction_value,
                                p.raw_probabilities
                            FROM predictions p
                            JOIN regions r ON p.region_id = r.region_id
                        """

            where_clause = ""
            if daily_fetcher:
                where_clause = "WHERE date = (SELECT MAX(date) FROM predictions)"
                print("Filtering PREDICTIONS data for the last available day.")

            sql_query = f"{base_query} {where_clause}"

            df = pd.read_sql(
                sql_query,
                self.connection,
                parse_dates=['date']
            )

            df['time'] = df['time'].apply(lambda x: str(x).split()[-1] if pd.notna(x) else None) 

            if df.empty:
                print("No data found.")
            else:
                print(f"Retrieved {len(df)} alert records.")

            return df

        except Error as e:
            print(f"Database error retrieving predictions: {e}")
            return pd.DataFrame()
        except Exception as e:
             print(f"An unexpected error occurred retrieving predictions: {e}")
             return pd.DataFrame()
            

    def get_isw_reports(self, daily_fetcher=False):
        """
        Retrieve ISW reports from the 'isw_reports' table.

        Args:
            daily_fetcher (bool): If True, retrieves reports only for the latest available date.
                                  If False (default), retrieves all reports.

        Returns:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            base_query = """
                SELECT date, content, url
                FROM isw_reports
            """

            where_clause = ""
            if daily_fetcher:
                where_clause = "WHERE date = (SELECT MAX(date) FROM isw_reports)"
                print("Filtering ISW data for the last available day.")

            order_by_clause = "ORDER BY date;"

            sql_query = f"{base_query} {where_clause} {order_by_clause}"
            
            return pd.read_sql(sql_query, self.connection, parse_dates=['date'])

        except Error as e:
            print(f"Database error retrieving ISW reports: {e}")
            return pd.DataFrame()
        except Exception as e:
             print(f"An unexpected error occurred retrieving ISW reports: {e}")
             return pd.DataFrame()


    def insert_telegram_report(self, df):
        """
        Insert or update Telegram reports from a DataFrame into the 'telegram_reports' table.

        Args:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            records = []

            for _, row in df.iterrows():
                date_val = row['date']
                content = row['message']
                records.append((date_val, content))

            cursor = self.connection.cursor()
            query = """
                INSERT INTO telegram_reports (date, content)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content)
            """
            cursor.executemany(query, records)
            self.connection.commit()
            print(f"Successfully inserted/handled {cursor.rowcount} telegram records.")
            cursor.close()

        except Error as e:
            print(f"Database error inserting Telegram reports: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting Telegram reports: {e}")

    def get_telegram_reports(self, daily_fetcher=False):
        """
        Retrieve Telegram reports from the 'telegram_reports' table.

        Args:
            daily_fetcher (bool): If True, retrieves reports only for the latest available date.
                                  If False (default), retrieves all reports.

        Returns:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            base_query = """
                SELECT date, content
                FROM telegram_reports
            """

            where_clause = ""
            if daily_fetcher:
                where_clause = "WHERE date = (SELECT MAX(date) FROM telegram_reports)"
                print("Filtering TELEGRAM data for the last available day.")

            sql_query = f"{base_query} {where_clause}"
            
            return pd.read_sql(sql_query, self.connection, parse_dates=['date'])

        except Error as e:
            print(f"Database error retrieving Telegram reports: {e}")
            return pd.DataFrame()
        except Exception as e:
             print(f"An unexpected error occurred retrieving Telegram reports: {e}")
             return pd.DataFrame()
            

    def get_weather_data(self, expand_json=True, daily_fetcher=False):
        """
        Retrieves weather data from the 'weather' table, optionally expanding the JSON 'data' column.

        Args:
            expand_json (bool): If True (default), parses the 'data' JSON column into separate DataFrame columns.
            daily_fetcher (bool): If True, retrieves weather data only for the latest available date.
                                  If False (default), retrieves all weather data.

        Returns:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            base_query = """
                SELECT
                    w.weather_id, w.region_id, r.region_name,
                    w.date, w.time, w.data
                FROM weather w
                JOIN regions r ON w.region_id = r.region_id
            """

            where_clause = ""
            if daily_fetcher:
                where_clause = "WHERE w.date = (SELECT MAX(date) FROM weather)"
                print("Filtering WEATHER data for the last available day.")

            order_by_clause = "ORDER BY r.region_name, w.date, w.time;"

            sql_query = f"{base_query} {where_clause} {order_by_clause}"

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
        Prepares weather DataFrame rows for insertion, converting row data to JSON.

        Args:
            df (pd.DataFrame): The input DataFrame containing weather data.
            region_mapping (dict): Maps region names (from df) to region IDs (for DB).
            col_mapping (dict): Maps standard keys ('region', 'date', 'time') to actual column names in df.

        Returns:
            list: A list of tuples, where each tuple is (region_id, date_value, time_value, json_data_string).
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
        Prepares alert DataFrame rows for insertion, converting row data to JSON.

        Args:
            df (pd.DataFrame): The input DataFrame containing alerts data.
            region_mapping (dict): Maps region names (from df) to region IDs (for DB).
            col_mapping (dict): Maps standard keys ('region', 'start_date', 'end_date')
                                to actual column names in df.

        Returns:
            list: A list of tuples, where each tuple is (region_id, start_datetime, end_datetime, json_data_string).
        """
        df = df.replace({float('nan'): None})  # !!!!!!!

        df['startDate'] = pd.to_datetime(df['startDate'], utc=True, format='mixed', errors='coerce')
        df['startDate'] = df['startDate'].dt.tz_convert('Europe/Kyiv')
        df['startDate'] = df['startDate'].dt.tz_localize(None)

        df['endDate'] = pd.to_datetime(df['endDate'], utc=True, format='mixed', errors='coerce')
        df['endDate'] = df['endDate'].dt.tz_convert('Europe/Kyiv')
        df['endDate'] = df['endDate'].dt.tz_localize(None)
        
        output = []

        for _, row in df.iterrows():
            region_value = row[col_mapping['region']]
            region_id = region_mapping.get(region_value)
            if region_id is None:
                print(f"Skipping unknown location: {region_value}")
                continue

            start = row[col_mapping['start_date']]
            end = row[col_mapping['end_date']]

            json_data_dict = row.to_dict()
            for key in col_mapping.values():
                json_data_dict.pop(key, None)
            json_data = json.dumps(json_data_dict, default=str)

            output.append((region_id, start, end, json_data))

        return output

    def insert_weather_data(self, df, region_mapping, col_mapping):
        """
        Prepares and inserts weather data into the 'weather' table.
        Updates existing records based on unique key (region_id, date, time).

        Args:
            df (pandas.DataFrame): DataFrame containing the raw weather data.
            region_mapping (dict): Dictionary mapping region names to region IDs.
            col_mapping (dict): Maps standard field names ('region', 'date', 'time')
                                to actual column names in the DataFrame.
        """
        try:
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
            print(f"Successfully inserted/handled {cursor.rowcount} weather records. Sanity check for daily runner: expected value is 600/0")
            cursor.close()

        except Error as e:
            print(f"Database error inserting weather data: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting weather data: {e}")

    def insert_alerts_data(self, df, region_mapping, col_mapping):
        """
        Prepares and inserts alerts data into the 'alarms' table.
        Ignores insertion if an alarm for the same region and start time already exists.

        Args:
            df (pandas.DataFrame): DataFrame containing the raw alerts data.
            region_mapping (dict): Dictionary mapping region names to region IDs.
            col_mapping (dict): Maps standard field names ('region', 'start_date', 'end_date')
                                to actual column names in the DataFrame.
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
    
            insert_sql = """
                INSERT IGNORE INTO alarms (region_id, start, end, data)
                    VALUES (%s, %s, %s, %s)
            """
    
            prepared = self.prepare_alerts_data(df, region_mapping, col_mapping)
            cursor.executemany(insert_sql, prepared)
            self.connection.commit()
            print(f"Successfully inserted/handled {cursor.rowcount} alarm records.")
            cursor.close()

        except Error as e:
            print(f"Database error inserting alarm data: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting alarm data: {e}")

    def insert_merged_data(self, df):
        """
        Inserts pre-processed/merged data into the 'merged_data' table.
        Extracts region_id, date, time, and stores the rest as JSON.
        Ignores insertion if data for the same region, date, and time already exists.

        Args:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect() 

            cursor = self.connection.cursor()
    
            df = df.replace({float('nan'): None})  # !!!!!!!
            records = []
    
            for _, row in df.iterrows():
                region_id_val = row['region_id']
                date_val = row['date']
                time_val = row['time']
    
                json_data_dict = row.to_dict()
                for key in ['region_id', 'date', 'time']:
                    json_data_dict.pop(key, None)
                json_data = json.dumps(json_data_dict, default=str)
    
                records.append((region_id_val, date_val, time_val, json_data))
    
            insert_sql = """
                INSERT IGNORE INTO merged_data (region_id, date, time, data)
                    VALUES (%s, %s, %s, %s)
            """
    
            cursor.executemany(insert_sql, records)
            self.connection.commit()
            print(f"Successfully inserted/handled merged dataset of {cursor.rowcount} rows. Sanity check for daily runner: expected value is 576/0")
            cursor.close()
            
        except Error as e:
            print(f"Database error inserting merged data: {e}")
        except Exception as e:
             print(f"An unexpected error occurred inserting merged data: {e}")


    def get_merged_data(self, col_map=None, daily_fetcher=False, expand_json=True):
        """
        Fetches data from 'merged_data' table, optionally expanding JSON and reordering columns.

        Args:
            col_map (list, optional): A list of column names defining the desired order.
                                      Columns not in the map are appended at the end. Defaults to None.
            daily_fetcher (bool): If True, retrieves data only for the latest available date.
                                  If False (default), retrieves all data.
            expand_json (bool): If True (default), parses the 'data' JSON column into separate DataFrame columns.

        Returns:
            df (pandas.DataFrame)
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect() 

            base_query = """
                    SELECT * FROM merged_data
                """
    
            where_clause = ""
            if daily_fetcher:
                where_clause = "WHERE date = (SELECT MAX(date) FROM merged_data)"
                print("Filtering MERGED data for the last available day.")
    
            sql_query = f"{base_query} {where_clause}"
    
            df = pd.read_sql(sql_query, self.connection, parse_dates=['date'])
            if expand_json and 'data' in df.columns:
                # unpack the JSON into separate columns
                json_records = [json.loads(s) for s in df['data']]
                expanded = pd.json_normalize(json_records)
                expanded.index = df.index
    
                base = df.drop(columns=['data'])
                base['time'] = base['time'].apply(lambda x: str(x).split()[-1] if pd.notna(x) else None)
    
                df = pd.concat([base, expanded], axis=1)
    
            else:
                df['time'] = df['time'].apply(lambda x: str(x).split()[-1] if pd.notna(x) else None)
    
            if col_map:
                cols_to_use = [c for c in col_map if c in df.columns]
                extra = [c for c in df.columns if c not in cols_to_use]
                df = df.reindex(columns=cols_to_use + extra)
    
            return df
            
        except Error as e:
            print(f"Database error retrieving merged data: {e}")
            return pd.DataFrame()
        except Exception as e:
             print(f"An unexpected error occurred retrieving merged data: {e}")
             return pd.DataFrame()


    def get_alerts(self, weekly_fetcher=False, validation_set=False):
        """
        Retrieves alert data from the 'alarms' table, joined with region names.

        Args:
            weekly_fetcher (bool): If True, retrieves alerts started within the last 7 days
                                   relative to the latest alert start time.
            validation_set (bool): If True, retrieves alerts only for the single latest date
                                   on which any alert started. Overrides weekly_fetcher if True.

        Returns:
            df (pandas.DataFrame)
        """

        try:
            if not self.connection or not self.connection.is_connected():
                self.connect() 

            base_query = """
                SELECT 
                    a.alarm_id, 
                    a.region_id, 
                    r.region_name, 
                    a.start, 
                    a.end, 
                    a.data
                FROM alarms a
                JOIN regions r ON a.region_id = r.region_id
            """

            where_clause = ""
            if weekly_fetcher:
                where_clause = "WHERE a.start >= (SELECT MAX(start) - INTERVAL 7 DAY FROM alarms)"

            if validation_set:
                where_clause = "WHERE DATE(a.start) = (SELECT MAX(DATE(start)) FROM alarms)"

            order_by_clause = "ORDER BY a.start DESC;"

            sql_query = f"{base_query} {where_clause} {order_by_clause}"

            df = pd.read_sql(
                sql_query,
                self.connection,
                parse_dates=['start', 'end']
            )

            if df.empty:
                print("No alarm data found.")
            else:
                print(f"Retrieved {len(df)} alert records.")

            return df

        except Error as e:
            print(f"Database error retrieving alerts: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred while retrieving alerts: {e}")
            return pd.DataFrame()
