# Ukraine Air Raid Forecast System

This project implements an automated system to forecast the likelihood of air raid alarms across various regions of Ukraine on an hourly basis. It serves as a functional tool designed to aid civilians in daily planning by providing advance notice of periods with heightened alarm risk.

**Current Status:** The system is operational, featuring an automated daily pipeline for data collection, processing, prediction using a tuned machine learning model, evaluation, and forecast delivery via a web API and JSON file output.

## Overview

The system uses multiple data sources to generate its forecasts:

* **Ukraine Alarm API:** Fetches official historical alarm start/end times.
* **Institute for the Study of War (ISW):** Scrapes daily "Russian Offensive Campaign Assessment" reports.
* **Telegram:** Monitors specific channels (e.g., `@war_monitor`) for relevant activity information.
* **Visual Crossing Weather API:** Retrieves hourly weather forecasts for regional centers.

Data is collected, processed, and stored in a MySQL database. An automated daily pipeline (`daily_forecast_orchestrator.py`) manages this workflow. Feature engineering includes creating lagged/summary alarm statistics, processing textual data from ISW and Telegram using NLP (TF-IDF + SVD), and deriving useful weather indicators.

A tuned **HistGradientBoostingClassifier** model, trained on historical data, generates hourly predictions for the probability of an alarm being active (`is_alarm_active`). These predictions are evaluated daily against actual outcomes, and the forecasts are made available through a basic Flask web application and API endpoint.

## Features

### Implemented

*   **Multi-Source Data Collection:** Integrates data from UkraineAlarm API, ISW website scraping, Telegram monitoring (`telethon`), and Visual Crossing Weather API.
*   **Centralized Database Storage:** Uses MySQL (`db_handler.py`) to store regions, raw/processed weather, ISW reports, Telegram messages, alarm history, merged features, model versions (including serialized blobs), predictions, and daily performance metrics.
*   **Historical Data Ingestion:**
    *   Scripts and database handler methods allow ingestion of data from Pandas DataFrames, enabling loading from CSV or other file formats.
    *   Flexible mapping system to handle different column names/structures in source files.
*   **Data Analysis & Preparation:**
    *   Performed Exploratory Data Analysis (EDA) on weather, alarm, and ISW datasets, including temporal patterns, regional differences, and distributions. (See `historical_weather_EDA.ipynb`, `historical_alarm_quality_and_EDA.ipynb`)
    *   Cleaned and standardized weather data, including outlier handling and imputation for missing visibility values. (See `historical_weather_quality_checks.ipynb`)
    *   Engineered hourly alarm features. (See `historical_alarm_quality_and_EDA.ipynb`)
    *   Processed ISW and Telegram reports using NLP: cleaning, lemmatization, stop-word removal. (See `isw_vectorization.ipynb` and  `telegram_vectorization.ipynb`)
    *   Vectorized ISW and Telegram reports using TF-IDF (unigrams & bigrams) and applied Truncated SVD for dimensionality reduction (150 components). (See `isw_vectorization.ipynb` and  `telegram_vectorization.ipynb`)
    *   Merged weather, alarm features, ISW SVD components and Telegram SVD components into a final hourly dataset. (See `final_dataset_refined.ipynb`)
*   **Modeling & Evaluation:**
    *   Split data using `TimeSeriesSplit` for chronologically sound training and testing. Scaled features using `StandardScaler`. Evaluated models using standard metrics (Accuracy, Precision, Recall, F1, ROC AUC) and confusion matrices. Tuned the models and identified top features based on model coefficients. (See `model_training_and_evaluation.ipynb` for linear and `training_and_evaluation.ipynb` for non-linear models)
* **Automated Daily Pipeline:** Orchestrated execution (`daily_forecast_orchestrator.py`) handling data fetching, processing, prediction, evaluation, and output generation.
* **Predictive Modeling:** Utilizes a tuned `HistGradientBoostingClassifier` (`hgb_v3`) optimized for high recall (target > 0.85) and acceptable precision (target >= 0.4). Model and associated scaler are stored in the database. (See `prediction_handler.py`)
* **Daily Prediction & Storage:** Generates hourly predictions and raw probabilities for each region daily, storing them in the `predictions` table.
* **Automated Evaluation:** Calculates daily performance metrics (Accuracy, Precision, Recall, F1, ROC AUC, Confusion Matrix) by comparing the previous day's predictions against actual alarm data and stores results in the `daily_metrics` table.
* **Forecast Output:**
    * Saves daily forecasts as a structured JSON file (`data/predictions/predictions_YYYY-MM-DD.json`).
    * Provides forecasts via a Flask API endpoint (`/api/v1/alarm-forecast`).
* **Web Interface:** Basic Flask application (`app.py`) serving an HTML page (`templates/index.html`) and the API.
* **(Prototype) Model Retraining:** Includes a module (`retrain_handler.py`) designed for weekly retraining, currently non-operational due to resource constraints.

## System Architecture

The system employs a modular Python structure:

1.  **Data Receivers (`src/data_receiver/`):** Modules for interacting with external sources (UkraineAlarm API, ISW, Telegram, Visual Crossing).
2.  **Database Handler (`src/database/db_handler.py`):** Manages all MySQL database operations.
3.  **Processing Pipeline (`src/pipeline/`):** Modules for cleaning, transforming, and engineering features from raw data (`alarm_processor.py`, `isw_processor.py`, `telegram_processor.py`, `weather_processor.py`).
4.  **Forecasting Engine (`src/forecasting/`):** Includes `prediction_handler.py` for applying the model and `retrain_handler.py` (prototype) for updates.
5.  **Orchestration (`src/forecasting/daily_forecast_orchestrator.py`):** Main script driving the daily workflow.
6.  **Frontend/API (`src/frontend/app.py`):** Flask application serving the web interface and API.
7.  **Database (MySQL):** Central data repository.
8.  **Artifacts (`artifacts/`):** Stores pre-trained TF-IDF vectorizers and SVD reducers for ISW and Telegram text processing.

*(See `docs/` folder for detailed Architecture, ERD, and Data Flow diagrams)*

## Technology Stack

| Category                | Technologies                                                             | Status                |
| :---------------------- | :----------------------------------------------------------------------- | :-------------------- |
| Language                | Python 3.8.0                                                             | Implemented           |
| Core Libraries          | `pandas`, `numpy`, `datetime`, `json`, `re`                              | Implemented           |
| Data Acquisition        | `requests`, `re`, `alerts_in_ua`                                         | Implemented           |
| Database                | AWS RDS (MySQL engine)                                                   | Implemented           |
| DB Connector            | `mysql-connector-python`                                                 | Implemented           |
| Cloud Platform          | AWS (EC2, RDS)                                                           | Implemented           |
| Scheduling              | `cron` (Linux)                                                           | Implemented           |
| Data Science            | `scikit-learn`, `matplotlib`, `seaborn`, `geopandas`                     | Implemented           |
| NLP                     | `nltk`, `ftfy`                                                           | Implemented           |
| Version Control         | Git                                                                      | Implemented           |
| Web Framework           | Flask                                                                    | Implemented           |
| App Server              | uWSGI                                                                    | Implemented           |

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8.0
    *   Git
    *   Access to an AWS account (for deploying EC2/RDS)
    *   MySQL client tools (optional, for direct DB access)

2.  **Clone Repository:**
    ```bash
    git clone https://github.com/teampds2025/Practice_2.git
    ```

3.  **Set Up Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **NLTK Data Download:**
    *   Run a Python interpreter: `python`
    *   Inside the interpreter, run:
        ```python
        import nltk
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('punkt')
        exit()
        ```

6.  **Configuration:**
    * Create a `.env` file in the project root directory.
    * Add the following environment variables with your credentials:
        ```dotenv
        DB_HOST=your_db_host_address
        DB_NAME=your_db_name
        DB_USER=your_db_username
        DB_PASSWORD=your_db_password
        DB_PORT=3306 

        ALARM_API_KEY=your_ukraine_alarm_api_key
        WEATHER_API_KEY=your_visual_crossing_api_key

        TELEGRAM_API_ID=your_telegram_api_id
        TELEGRAM_API_HASH=your_telegram_api_hash

        ALERTSAPP_TOKEN=your_chosen_secret_token_for_flask_api
        ```

7.  **Database Setup:**
    *   Ensure your RDS instance is running and accessible.
    *   Use the `DatabaseHandler` class to:
        *   Create tables: `db.create_tables()`
        *   Initialize regions: `db.initialize_regions_in_database()`

8.  **Running Collectors Manually (for testing):**
    *   Refer to the example notebooks (e.g., `receive_and_load.ipynb`) for using collectors and interacting with the database.

9. **Historical Data Ingestion:**
    *   Place historical CSV files in a known location.
    *   Adapt scripts from example notebooks, defining `region_mapping` and `col_mapping` as needed, to read files into DataFrames and use `db.insert_..._data()` methods.

10.  **Running the System:**
    * **Daily Pipeline:** Run the orchestrator script:
        ```bash
        python -m src.forecasting.daily_forecast_orchestrator
        ```
        *Note: The first run might require Telegram authentication via console input.*
        Schedule this script using `cron` or another task scheduler for automated daily execution.
      
11. **Data Analysis & Modeling Notebooks:**
    *   The repository contains Jupyter notebooks detailing the all operations performed, see `notebooks/`

## Usage

1.  **Automated Daily Run:** Set up a scheduler (`cron`) to run `src.forecasting.daily_forecast_orchestrator` daily.
2.  **Check Output File:** Find the latest forecast JSON in the `data/predictions/` directory.
3.  **Access Web Interface:** Start the Flask app (`src.frontend.app`)
4.  **Use API Endpoint:** Send a POST request to `/api/v1/alarm-forecast` with a JSON body containing your `ALERTSAPP_TOKEN` and optionally a `region` field. 
5.  **Database Inspection:** Connect to the MySQL database to view raw data, merged features, predictions, models, and metrics directly.
