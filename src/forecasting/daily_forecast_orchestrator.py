from src.pipeline.weather_processor import get_and_process_weather
from src.pipeline.alarm_processor import get_and_process_alarms, get_and_process_validation_set
from src.pipeline.isw_processor import get_and_process_isw_reports
from src.pipeline.telegram_processor import get_and_process_telegram_reports
from src.forecasting.prediction_handler import process_daily_predictions
from src.database.db_handler import DatabaseHandler
from dotenv import load_dotenv
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
import warnings

# suppress a specific UserWarning from pandas related to SQLAlchemy
warnings.filterwarnings(
    "ignore",
    message=".*pandas only supports SQLAlchemy connectable.*",
    category=UserWarning,
)

# we use async here to ensure that modules related to Telegram data collection work properly 
# (due to the specifics of the telethon library)
async def prepare_final_dataset(): 
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
    print("\n===== DATABASE CONNECTION ESTABLISHED =====")

    today_target_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    yesterday_target_date = today_target_date - timedelta(days=1)
    timestamp_for_filename = today_target_date.strftime("%Y-%m-%d")
    timestamp_for_metrics = pd.Timestamp(yesterday_target_date)
    print(f"\n===== TARGET DATETIME: {timestamp_for_filename} =====")
    
    print("\n===== STEP 1: PROCESSING WEATHER =====")
    weather_prepared = get_and_process_weather(today_target_date, db)

    
    print("\n===== STEP 2: PROCESSING ALARM FEATURES =====")
    alarms_features_prepared = get_and_process_alarms(today_target_date, db)

    
    print("\n===== STEP 3: PROCESSING ISW REPORTS =====")
    isw_prepared = get_and_process_isw_reports(yesterday_target_date, db)

    
    print("\n===== STEP 4: PROCESSING TELEGRAM REPORTS =====")
    telegram_prepared  = await get_and_process_telegram_reports(yesterday_target_date, db)

    
    print("\n===== STEP 5: MERGING FINAL DATASET =====")
    weather_prepared['datetime'] = pd.to_datetime(weather_prepared['datetime'], errors='coerce')
    alarms_features_prepared['datetime'] = pd.to_datetime(alarms_features_prepared['datetime'], errors='coerce')
    isw_prepared['date'] = pd.to_datetime(isw_prepared['date'], errors='coerce').dt.normalize()
    telegram_prepared['date'] = pd.to_datetime(telegram_prepared['date'], errors='coerce').dt.normalize()

    # we use yesterday's reports for today's predictions
    isw_prepared['date'] = isw_prepared['date'] + pd.Timedelta(days=1) 
    telegram_prepared['date'] = telegram_prepared['date'] + pd.Timedelta(days=1) 
    
    merged_v1 = pd.merge(
        alarms_features_prepared,
        weather_prepared,
        left_on=['region_id', 'datetime'],
        right_on=['region_id', 'datetime'],
        how='left'
    )
    merged_v1['date_for_merge'] = merged_v1['datetime'].dt.normalize()
    merged_v2 = pd.merge(
        merged_v1,
        isw_prepared,
        left_on='date_for_merge',
        right_on='date',
        how='left'
    )
    merged_v3 = pd.merge(
        merged_v2,
        telegram_prepared,
        left_on='date_for_merge',
        right_on='date',
        how='left'
    )
    
    merged_v3 = merged_v3.sort_values(by=['datetime', 'region_id']).reset_index(drop=True)
    merged_v3['datetime'] = pd.to_datetime(merged_v3['datetime'], errors='coerce')
    merged_v3['hour_of_day'] = merged_v3['datetime'].dt.hour
    merged_v3['day_of_week'] = merged_v3['datetime'].dt.dayofweek
    merged_v3['month'] = merged_v3['datetime'].dt.month

    db.insert_merged_data(merged_v3)

    # we get predictions for yesterday and evaluate them based on the actual alarm information that happened yesterday that we got today.
    predictions_validate = db.get_predictions(daily_fetcher=True) 
    
    print("\n===== STEP 6: PROCESSING DAILY PREDICTIONS =====")
    process_daily_predictions(merged_v3, db)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    predictions_dir_abs = os.path.join(project_root, 'data', 'predictions')
    json_filename = f"predictions_{timestamp_for_filename}.json"
    json_filepath_abs = os.path.join(predictions_dir_abs, json_filename)
    
    predictions_for_today = db.get_predictions(daily_fetcher=True)
    predictions_for_today['time'] = predictions_for_today['time'].str.slice(0, 5)
    predictions_for_today['prediction_value'] = predictions_for_today['prediction_value'].astype(bool)
    result = (
        predictions_for_today.groupby('region_name')
        .apply(lambda x: dict(zip(x['time'], x['prediction_value'])))
        .to_dict()
    )
    
    final_json = {"regions_forecast": result}

    os.makedirs(predictions_dir_abs, exist_ok=True)
    with open(json_filepath_abs, "w", encoding='utf-8') as f:
        json.dump(final_json, f, indent=2)

    
    print("\n===== STEP 7: EVALUATING YESTERDAY'S PREDICTIONS =====")    
    if predictions_validate.empty: 
        print('The metrics table is empty. Metric evaluation will likely start tomorrow. Skipping step 7 by now.')
    elif predictions_validate['date'][0] != timestamp_for_metrics:
        last_metric_date = predictions_validate['date'][0]
        print(f'Latest metric is calculated for {last_metric_date.strftime("%Y-%m-%d")}, '
              f'while we need {timestamp_for_metrics.strftime("%Y-%m-%d")}. Skipping step 7 by now.')
    else:
        actual_alarm_set = get_and_process_validation_set(db)
    
        actual_values = actual_alarm_set['is_alarm_active'].to_numpy()
        predicted_values = predictions_validate['prediction_value'].to_numpy()
        probabilities = predictions_validate['raw_probabilities'].to_numpy()
    
        accuracy = accuracy_score(actual_values, predicted_values)
        precision = precision_score(actual_values, predicted_values, zero_division=0)
        recall = recall_score(actual_values, predicted_values, zero_division=0)
        if precision + recall == 0:
            f1_score = 0
        else:
            f1_score = 2 * precision * recall / (precision + recall) # calculating manually to prevent naming errors
        roc_auc = roc_auc_score(actual_values, probabilities)
        conf_matrix = confusion_matrix(actual_values, predicted_values)
        conf_matrix_json = json.dumps(conf_matrix.tolist())
        db.insert_metrics(today_target_date, 'hgb_v1', accuracy, precision, recall, f1_score, roc_auc, conf_matrix_json)

    print("\n===== DATABASE CONNECTION CLOSED =====")  
    db.disconnect()
    

if __name__ == "__main__":
    asyncio.run(prepare_final_dataset())