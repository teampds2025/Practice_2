import pandas as pd
import pickle
import json

def process_daily_predictions(df, db_handler):
    """or we can use
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
    df = db_handler.get_merged_data(col_map=col_map)
    """

    mod, scal = db_handler.get_model_by_version('hgb_v3')
    loaded_model = pickle.loads(mod)
    loaded_scaler = pickle.loads(scal)
    
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
    X_scaled = loaded_scaler.transform(X)
    
    probabilities = loaded_model.predict_proba(X_scaled)
    probabilities = probabilities[:, 1]
    custom_predictions = probabilities > 0.45
    custom_predictions_applied = custom_predictions.astype(int)
    
    df['is_alarm_active'] = custom_predictions_applied
    df['raw_probabilities'] = probabilities
    predictions_result_table = df[['region_id', 'date', 'time', 'is_alarm_active', 'raw_probabilities']]
    db_handler.insert_predictions(predictions_result_table)