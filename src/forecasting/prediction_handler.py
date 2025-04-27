import pandas as pd
import pickle
import json

def process_daily_predictions(df, db_handler):
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
