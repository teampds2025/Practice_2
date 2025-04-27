from dotenv import load_dotenv
import os
from src.database.db_handler import DatabaseHandler
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier
from datetime import datetime
import pytz
import pickle

"""
It is planned that this module will be responsible for retraining the model every week based 
on the new data received during that week. At the moment, this module is in prototype status 
and is not executed due to technical limitations - ec2 instance in current configuration is 
not able to process data volumes similar to our merged dataset due to lack of RAM. 

At the moment, we can consider our project as MVP - it has enough features to be usable by early 
customers, and potential additional features like model retraining can be realized in the future.
"""

def retrain_model_weekly():
    load_dotenv()
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_port = os.environ.get("DB_PORT")
    db = DatabaseHandler(
     host=db_host,
     database=db_name,
     user=db_user,
     password=db_password,
     port=db_port
    )
    db.connect()


    col_map = ['region_id',
     'time_since_last_alarm_end_minutes_at_start_of_day',
     'total_alarm_minutes_yesterday',
     'alarms_started_yesterday',
     'alarms_started_trend',
     'was_alarm_active_end_of_yesterday',
     'is_alarm_active_lag_7d',
     'avg_daily_alarm_minutes_last_7_days',
     'dew',
     'snow',
     'temp',
     'precip',
     'tempmax',
     'tempmin',
     'winddir',
     'humidity',
     'pressure',
     'windgust',
     'moonphase',
     'snowdepth',
     'windspeed',
     'cloudcover',
     'visibility',
     'precipcover',
     'precipprob_binary',
     'rain_bin',
     'snow_bin',
     'rain_snow_bin',
     'sunrise_seconds',
     'sunset_seconds',
     'daylight_duration_seconds',
     'svd_comp_1',
     'svd_comp_2',
     'svd_comp_3',
     'svd_comp_4',
     'svd_comp_5',
     'svd_comp_6',
     'svd_comp_7',
     'svd_comp_8',
     'svd_comp_9',
     'svd_comp_10',
     'svd_comp_11',
     'svd_comp_12',
     'svd_comp_13',
     'svd_comp_14',
     'svd_comp_15',
     'svd_comp_16',
     'svd_comp_17',
     'svd_comp_18',
     'svd_comp_19',
     'svd_comp_20',
     'svd_comp_21',
     'svd_comp_22',
     'svd_comp_23',
     'svd_comp_24',
     'svd_comp_25',
     'svd_comp_26',
     'svd_comp_27',
     'svd_comp_28',
     'svd_comp_29',
     'svd_comp_30',
     'svd2_comp_1',
     'svd2_comp_2',
     'svd2_comp_3',
     'svd2_comp_4',
     'svd2_comp_5',
     'svd2_comp_6',
     'svd2_comp_7',
     'svd2_comp_8',
     'svd2_comp_9',
     'svd2_comp_10',
     'svd2_comp_11',
     'svd2_comp_12',
     'svd2_comp_13',
     'svd2_comp_14',
     'svd2_comp_15',
     'svd2_comp_16',
     'svd2_comp_17',
     'svd2_comp_18',
     'svd2_comp_19',
     'svd2_comp_20',
     'svd2_comp_21',
     'svd2_comp_22',
     'svd2_comp_23',
     'svd2_comp_24',
     'svd2_comp_25',
     'svd2_comp_26',
     'svd2_comp_27',
     'svd2_comp_28',
     'svd2_comp_29',
     'svd2_comp_30',
     'hour_of_day',
     'day_of_week',
     'month']

    df = db.get_merged_data(col_map=col_map)

    target_column = 'is_alarm_active'

    potential_features = df.columns.tolist()
    features_to_exclude = [
        target_column,
        'datetime',
        'date_x',
        'date_y',
        'time',
        'date',
        'date_value',
        'date_for_merge',
        'time_value',
        'severerisk',
        'report_id'
    ]

    feature_columns = [col for col in potential_features if col not in features_to_exclude]

    X = df[feature_columns]
    y = df[target_column]

    final_scaler = StandardScaler()
    final_model_hgb = HistGradientBoostingClassifier(
     loss='log_loss',
     learning_rate=0.01,
     max_iter=400,
     max_leaf_nodes=61,
     max_depth=None,
     l2_regularization=0.5,
     class_weight='balanced',
     early_stopping=True,
     validation_fraction=0.2,
     n_iter_no_change=30,
     min_samples_leaf=40,
     random_state=1
    )
    X_scaled_final = final_scaler.fit_transform(X)
    final_model_hgb.fit(X_scaled_final, y)

    model_blob = pickle.dumps(final_model_hgb)
    scaler_blob = pickle.dumps(final_scaler)

    kyiv_tz = pytz.timezone('Europe/Kyiv')
    now_with_timezone = datetime.now(kyiv_tz)
    formatted_time = now_with_timezone.strftime('%Y-%m-%dT%H:%M:%SZ')
    formatted_version = now_with_timezone.strftime('%Y%m%d') + '_v'

    db.insert_model('HistGradientBoostingClassifier', formatted_version, formatted_time, model_blob, scaler_blob)


if  __name__ == '__main__':
    retrain_model_weekly()