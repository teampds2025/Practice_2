# Ukraine War Event Prediction System (Prototype)

This project aims to design and implement a system for predicting war-related events (specifically air raids) in regions of Ukraine.

**Current Status:** This is a functional prototype. The data collection pipeline and storage infrastructure are implemented. Exploratory data analysis, data preparation, feature engineering, and initial baseline modeling (Linear/Logistic Regression) have been completed.

## Overview

The system automates the collection of data from various sources:

*   **Institute for the Study of War (ISW):** Daily "Russian Offensive Campaign Assessment" reports scraped from their website.
*   **Weather Data:** Historical and forecasted hourly weather data for regional centers, enriched with daily metrics (via Visual Crossing API).
*   **Air Raid Alerts:** Historical and active alerts via the `alerts_in_ua` Python library (or historical CSV).
*   **Historical Files:** Ingestion support for historical ISW reports, weather, and alert data from CSV files.

Collected data is structured and stored in a relational database (MySQL on AWS RDS). This historical archive was used for analysis and initial model training. The ultimate goal remains to develop refined predictive models capable of forecasting relevant events within a 24-hour timeframe to enhance situational awareness.

## Features

### Implemented

*   **Data Collection:**
    *   Automated scraping of ISW daily reports.
    *   Fetching of hourly weather data (historical & forecast) via API.
    *   Retrieval of active air raid alerts using `alerts_in_ua`.
*   **Data Storage:**
    *   Relational database schema on AWS RDS (MySQL) for `regions`, `weather`, `isw_reports`, `alerts`.
    *   Use of `JSON` data type for storing detailed weather metrics and raw alert information.
*   **Historical Data Ingestion:**
    *   Scripts and database handler methods allow ingestion of data from Pandas DataFrames, enabling loading from CSV or other file formats.
    *   Flexible mapping system to handle different column names/structures in source files.
*   **Data Analysis & Preparation:**
    *   Performed Exploratory Data Analysis (EDA) on weather, alarm, and ISW datasets, including temporal patterns, regional differences, and distributions. (See `historical_weather_EDA.ipynb`, `historical_alarm_quality_and_EDA.ipynb`)
    *   Cleaned and standardized weather data, including outlier handling and imputation for missing visibility values. (See `historical_weather_quality_checks.ipynb`)
    *   Engineered hourly alarm features: `is_alarm_active` (target), `alarm_minutes_in_hour`, `alarms_started_in_hour`, `time_since_last_alarm_end_minutes`. (See `historical_alarm_quality_and_EDA.ipynb`)
    *   Processed ISW reports using NLP: cleaning, lemmatization, stop-word removal. (See `isw_vectorization.ipynb`)
    *   Vectorized ISW reports using TF-IDF (unigrams & bigrams) and applied Truncated SVD for dimensionality reduction (150 components). (See `isw_vectorization.ipynb`)
    *   Merged weather, alarm features, and ISW SVD components into a final hourly dataset. (See `final_dataset_preparing.ipynb`)
*   **Modeling & Evaluation:**
    *   Split data using `TimeSeriesSplit` for chronologically sound training and testing. (See `model_training_and_evaluation.ipynb`)
    *   Scaled features using `StandardScaler`. (See `model_training_and_evaluation.ipynb`)
    *   Trained baseline models: Linear Regression and Logistic Regression (using `class_weight='balanced'` to handle imbalance). (See `model_training_and_evaluation.ipynb`)
    *   Evaluated models using standard metrics (Accuracy, Precision, Recall, F1, ROC AUC) and confusion matrices. (See `model_training_and_evaluation.ipynb`)
    *   Performed initial threshold tuning for Logistic Regression based on Precision-Recall curve analysis (selected threshold 0.3). (See `model_training_and_evaluation.ipynb`)
    *   Identified top features based on model coefficients. (See `model_training_and_evaluation.ipynb`)
*   **Basic Infrastructure:**
    *   Modular Python code structure.
    *   Configuration for database and API credentials.
    *   Setup scripts/methods for database table creation and region initialization.
    *   Designed for EC2 deployment with `cron` for scheduling.

### Planned

*   **Further Feature Engineering:**
    *   Refining NLP features from ISW reports.
    *   Creating more complex time-based features (e.g., rolling averages, lags).
    *   Exploring interactions between different data sources.
*   **Prediction Generation:**
    *   Scheduled task to generate 24-hour forecasts per region using the best model.
    *   Storing predictions in a dedicated database table.
*   **Web Application:**
    *   Flask backend API to serve data and predictions.
    *   HTML/CSS/JS frontend for users to view collected data and forecasts.
    *   Deployment using uWSGI.

## System Architecture

The system follows a modular design:

1.  **External Data Sources:** APIs (Weather, Alerts) and Websites (ISW), File archives (CSV).
2.  **Data Receiver Module (EC2):** Python scripts (`ISWDataCollector`, `WeatherDataCollector`, `AlertsAPIHandler`) responsible for fetching and preparing data. Includes a daily runner script triggered by `cron`. Handles file ingestion logic.
3.  **Database (AWS RDS - MySQL):** Central persistent storage for all collected raw and processed data. Managed via `DatabaseHandler`.
4.  **Forecasting Module (EC2):** Contains scripts for feature engineering, model training/evaluation, and prediction generation (partially implemented).
5.  **Web Application (EC2 - Planned):** Flask backend and basic frontend for user interaction.

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
| **Planned**             |                                                                          |                       |
| Web Framework           | Flask                                                                    | Planned               |
| App Server              | uWSGI                                                                    | Planned               |

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
    *   Set environment variables or use a `.env` file (requires `python-dotenv` package) for:
        *   `DB_HOST`: Your AWS RDS endpoint URL
        *   `DB_NAME`: Your database name
        *   `DB_USER`: Your database username
        *   `DB_PASS`: Your database password
        *   `DB_PORT`: Database port (default: 3306)
        *   `WEATHER_API_KEY`: Your API key for the weather service (e.g., Visual Crossing)
        *   `ALERTS_API_TOKEN`: Your API token for the `alerts_in_ua` service

7.  **Database Setup:**
    *   Ensure your RDS instance is running and accessible.
    *   Use the `DatabaseHandler` class (or provided setup script if available) to:
        *   Create tables: `db.create_tables()`
        *   Initialize regions: `db.initialize_regions_in_database()`

8.  **Running Collectors Manually (for testing):**
    *   Refer to the example notebooks (e.g., `receive_and_load.ipynb`) for using collectors and interacting with the database.

9.  **Scheduling with Cron (on EC2):**
    *   Create a main runner script (e.g., `daily_runner.py`) to orchestrate daily data collection.
    *   Set up a cron job to execute this script.

10. **Historical Data Ingestion:**
    *   Place historical CSV files in a known location.
    *   Adapt scripts from example notebooks, defining `region_mapping` and `col_mapping` as needed, to read files into DataFrames and use `db.insert_..._data()` methods.

11. **Data Analysis & Modeling Notebooks:**
    *   The repository contains Jupyter notebooks detailing the EDA, data preparation, and initial modeling steps performed in Assignment 3:
        *   `historical_weather_quality_checks.ipynb`
        *   `historical_weather_EDA.ipynb`
        *   `historical_alarm_quality_and_EDA.ipynb`
        *   `isw_vectorization.ipynb`
        *   `final_dataset_preparing.ipynb`
        *   `model_training_and_evaluation.ipynb`

## Usage

Current interactions:

1.  **Data Collection:** Via scheduled `cron` job or manual execution of collector scripts/notebooks.
2.  **Database Inspection:** Direct SQL queries to the RDS database.
3.  **Analysis/Modeling Review:** Examining the provided Jupyter notebooks.

The planned web interface will offer a more user-friendly experience.

## Future Work

*   Implement Further Feature Engineering pipeline.
*   Build the Flask backend API.
*   Create the frontend user interface.
*   Implement prediction storage and retrieval.
*   Add comprehensive logging and monitoring.
*   Refine error handling and data validation.
