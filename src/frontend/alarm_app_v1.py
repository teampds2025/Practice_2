import datetime as dt
from dotenv import load_dotenv
import json
import os
import requests
from flask import Flask, jsonify, request, render_template
import pandas as pd 
from src.database.db_handler import DatabaseHandler
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

load_dotenv()
API_TOKEN = os.environ.get("ALERTSAPP_TOKEN")
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

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def alarm_forecast_page():
    token_for_frontend = API_TOKEN
    if not token_for_frontend:
        return "API Token missing.", 500

    return render_template('index.html', api_token_value=token_for_frontend)

@app.route('/api/v1/alarm-forecast', methods=['POST'])
def get_alarm_forecast_api():
    data = request.get_json()

    if not data: 
        raise InvalidUsage("Request body must contain JSON data", status_code=400)

    if data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    target_region_input = data.get('region', 'all')
    if not target_region_input:
        target_region_input = 'all'

    try:
        predictions_df_all = db.get_predictions(daily_fetcher=True)

        if predictions_df_all.empty:
            raise InvalidUsage("No prediction data available.", status_code=404)

        model_info = db.get_model_info(daily_fetcher=True)
        last_train_time = pd.to_datetime(model_info['last_trained_on'].iloc[0]).strftime('%Y-%m-%dT%H:%M:%SZ') if not model_info.empty else None

        predictions_df_all['datetime'] = pd.to_datetime(predictions_df_all['date'].astype(str) + ' ' + predictions_df_all['time'])
        last_pred_time = predictions_df_all['datetime'].max().strftime('%Y-%m-%dT%H:%M:%SZ') if not predictions_df_all.empty else None

        predictions_df_filtered = predictions_df_all 

        if target_region_input.lower() != 'all':
            requested_regions = [r.strip().lower() for r in target_region_input.split(',') if r.strip()]

            if not requested_regions:
                target_region_input = 'all'

            else:
                predictions_df_filtered = predictions_df_all[
                    predictions_df_all['region_name'].str.lower().isin(requested_regions)
                ]

                if predictions_df_filtered.empty:
                    raise InvalidUsage(f"No forecast data found for region(s): {target_region_input}", status_code=404)

        regions_forecast = {}

        predictions_df_filtered['time_formatted'] = pd.to_datetime(predictions_df_filtered['time'], format='%H:%M:%S').dt.strftime('%H:%M')
        predictions_df_filtered['prediction_bool'] = predictions_df_filtered['prediction_value'].astype(bool)

        for region, group in predictions_df_filtered.groupby('region_name'):
            region_data = {row['time_formatted']: row['prediction_bool']
                           for _, row in group.sort_values('time_formatted').iterrows()}
            regions_forecast[region] = region_data

        response_data = {
            "last_model_train_time": last_train_time,
            "last_prediction_time": last_pred_time, 
            "regions_forecast": regions_forecast
        }

        return jsonify(response_data)

    except InvalidUsage as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise InvalidUsage("An internal server error occurred.", status_code=500)
