import pandas as pd
from dotenv import load_dotenv
import os
from src.data_receiver.alarms_receiver import UkraineAlarmAPIClient
from datetime import datetime, timedelta

def get_and_process_alarms(target_date, db_handler):

    load_dotenv()
    alarm_api_key = os.environ.get("ALARM_API_KEY")

    yesterday_target_date = target_date - timedelta(days=1)
    
    client = UkraineAlarmAPIClient(api_key=alarm_api_key)
    history = client.get_date_history(yesterday_target_date) # in datetime(Y, M, D) format
    
    col_mapping = {
        'region': 'regionName',
        'start_date': 'startDate',
        'end_date': 'endDate',
    }
    region_mapping = {
        'м. Київ': 1,
        'Київська область': 2,
        'Вінницька область': 3,
        'Волинська область': 4,
        'Дніпропетровська область': 5,
        'Донецька область': 6,
        'Житомирська область': 7,
        'Закарпатська область': 8,
        'Запорізька область': 9,
        'Івано-Франківська область': 10,
        'Кіровоградська область': 11,
        'Луганська область': 12,
        'Львівська область': 13,
        'Миколаївська область': 14,
        'Одеська область': 15,
        'Полтавська область': 16,
        'Рівненська область': 17,
        'Сумська область': 18,
        'Тернопільська область': 19,
        'Харківська область': 20,
        'Херсонська область': 21,
        'Хмельницька область': 22,
        'Черкаська область': 23,
        'Чернівецька область': 24,
        'Чернігівська область': 25,
    }
    db_handler.insert_alerts_data(history, region_mapping, col_mapping)

    alarms_df = db_handler.get_alerts(weekly_fetcher=True)
    
    alarms_df.dropna(subset=['start', 'end'], inplace=True) # filter for empty values
    alarms_df = alarms_df[alarms_df['start'] <= alarms_df['start'].max().normalize()] # filter to prevent potentional data leakage
    
    alarms_df.sort_values(by=['region_id', 'start'], inplace=True)
    alarms_df = alarms_df[['region_id', 'start', 'end']].copy()
    
    min_date = alarms_df['start'].min().normalize()
    max_date = pd.Timestamp(target_date) # in Timestamp('Y-M-D 00:00:00') format
    
    feature_dates = pd.date_range(start=min_date,
                                  end=max_date,
                                  freq='D')
    results_daily = []
    results_hourly = []
    
    grouped_alarms = alarms_df.groupby('region_id')
    
    for region_id, region_alarms in grouped_alarms:
        region_alarms = region_alarms.sort_values(by='start')
    
        # daily processing
        for current_day in feature_dates:
            start_of_day = current_day
            start_of_yesterday = start_of_day - pd.Timedelta(days=1)
            start_of_day_before_yesterday = start_of_day - pd.Timedelta(days=2)
            end_of_yesterday = start_of_day - pd.Timedelta(microseconds=1)  # very end of previous day
            start_of_7_days_ago = start_of_day - pd.Timedelta(days=7)
    
            # time_since_last_alarm_end_minutes_at_start_of_day
            alarms_ended_before_today = region_alarms[region_alarms['end'] < start_of_day]
            if not alarms_ended_before_today.empty:
                last_alarm_end_time = alarms_ended_before_today['end'].max()
                time_since_last_end = (start_of_day - last_alarm_end_time).total_seconds() / 60
            else:
                time_since_last_end = pd.NA
    
            # total_alarm_minutes_yesterday
            yesterday_overlap = region_alarms[
                (region_alarms['start'] < start_of_day) & (region_alarms['end'] > start_of_yesterday)
            ]
            total_minutes_yesterday = 0
            for _, alarm in yesterday_overlap.iterrows():
                intersection_start = max(alarm['start'], start_of_yesterday)
                intersection_end = min(alarm['end'], start_of_day)
                duration_yesterday = (intersection_end - intersection_start).total_seconds() / 60
                if duration_yesterday > 0:
                    total_minutes_yesterday += duration_yesterday
    
            # alarms_started_yesterday
            alarms_started_yesterday_count = region_alarms[
                (region_alarms['start'] >= start_of_yesterday) & (region_alarms['start'] < start_of_day)
            ].shape[0]
    
            # was_alarm_active_end_of_yesterday
            was_active_end_of_yesterday = region_alarms[
                (region_alarms['start'] <= end_of_yesterday) & (region_alarms['end'] > end_of_yesterday)
            ].shape[0] > 0
    
            # alarms_started_trend
            alarms_started_day_before_yesterday_count = region_alarms[
                (region_alarms['start'] >= start_of_day_before_yesterday) & (region_alarms['start'] < start_of_yesterday)
            ].shape[0]
    
            alarms_started_trend = alarms_started_yesterday_count - alarms_started_day_before_yesterday_count
    
            # is_alarm_active_lag_7d
            is_active_start_7d_ago = region_alarms[
                (region_alarms['start'] <= start_of_7_days_ago) & (region_alarms['end'] > start_of_7_days_ago)
            ].shape[0] > 0
    
            # avg_daily_alarm_minutes_last_7_days
            total_minutes_last_7d = 0
            days_to_check = 7
            for i in range(1, days_to_check + 1):
                day_start = start_of_day - pd.Timedelta(days=i)
                day_end = day_start + pd.Timedelta(days=1)
                day_overlap = region_alarms[
                    (region_alarms['start'] < day_end) & (region_alarms['end'] > day_start)
                ]
                minutes_this_day = 0
                for _, alarm in day_overlap.iterrows():
                    intersection_start = max(alarm['start'], day_start)
                    intersection_end = min(alarm['end'], day_end)
                    duration = (intersection_end - intersection_start).total_seconds() / 60
                    if duration > 0:
                        minutes_this_day += duration
                total_minutes_last_7d += minutes_this_day
            avg_minutes_last_7d = total_minutes_last_7d / days_to_check if days_to_check > 0 else 0
    
            daily_features = {
                'region_id': region_id,
                'date': start_of_day.date(),
                'time_since_last_alarm_end_minutes_at_start_of_day': time_since_last_end,
                'total_alarm_minutes_yesterday': total_minutes_yesterday,
                'alarms_started_yesterday': alarms_started_yesterday_count,
                'alarms_started_trend': alarms_started_trend,
                'was_alarm_active_end_of_yesterday': was_active_end_of_yesterday,
                'is_alarm_active_lag_7d': is_active_start_7d_ago,
                'avg_daily_alarm_minutes_last_7_days': avg_minutes_last_7d,
            }
            results_daily.append(daily_features.copy())
    
            # hourly processing
            for hour in range(24):
                hour_timestamp = start_of_day + pd.Timedelta(hours=hour)
                hour_end_timestamp = hour_timestamp + pd.Timedelta(hours=1)
                
                is_active = int(region_alarms[
                    (region_alarms['start'] < hour_end_timestamp) &
                    (region_alarms['end'] > hour_timestamp)
                ].shape[0] > 0)
    
                hourly_record = daily_features.copy()
                hourly_record.update({
                    'hour_indicator': hour_timestamp.time(),
                    'is_alarm_active': is_active
                })
                results_hourly.append(hourly_record)
    
    
    hourly_features_df = pd.DataFrame(results_hourly)
    
    hourly_features_df['date'] = pd.to_datetime(hourly_features_df['date'])
    hourly_features_df['datetime'] = hourly_features_df['date'].dt.normalize() + pd.to_timedelta(
        hourly_features_df['hour_indicator'].astype(str)
    )

    alarms_features_prepared = hourly_features_df[hourly_features_df['date'] == target_date]
    
    alarms_features_prepared = alarms_features_prepared.drop(columns=['date', 'hour_indicator'])
    
    return alarms_features_prepared

def get_and_process_validation_set(db_handler):
    alarms_df = db_handler.get_alerts(validation_set=True) 
    
    alarms_df.sort_values(by=['region_id', 'start'], inplace=True)
    alarms_df = alarms_df[['region_id', 'start', 'end']].copy()
    
    results_hourly = []
    
    all_region_ids = [i for i in range(1, 26) if i != 12] # Luhansk
    unique_day = alarms_df['start'].min().normalize()
    grouped_alarms = alarms_df.groupby('region_id')
    regions_with_alarms = set(grouped_alarms.groups.keys())
    
    for region_id in all_region_ids:
        for hour in range(24):
            hour_timestamp = unique_day + pd.Timedelta(hours=hour)
            hour_end_timestamp = hour_timestamp + pd.Timedelta(hours=1)
    
            is_active = 0 
    
            if region_id in regions_with_alarms:
                region_alarms = grouped_alarms.get_group(region_id)
    
                is_active = int(region_alarms[
                    (region_alarms['start'] < hour_end_timestamp) &
                    (region_alarms['end'] > hour_timestamp)
                ].shape[0] > 0)
    
            hourly_record = {
                'region_id': region_id,
                'hour_indicator': hour_timestamp.time(),
                'is_alarm_active': is_active
                }
            results_hourly.append(hourly_record)
    
    return pd.DataFrame(results_hourly)