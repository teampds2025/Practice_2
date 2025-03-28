# Ukraine War Event Prediction System (Prototype)

This project aims to design and implement a system for predicting war-related events (specifically air raids, artillery shelling, and urban fights based on `alerts_in_ua` data) in selected regions of Ukraine. 

**Current Status:** This is a functional prototype focused on the data collection pipeline and storage infrastructure. The predictive modeling and user interface components are planned for future development.

## Overview

The system automates the collection of data from various sources:

*   **Institute for the Study of War (ISW):** Daily "Russian Offensive Campaign Assessment" reports scraped from their website.
*   **Weather Data:** Historical and forecasted hourly weather data for regional centers, enriched with daily metrics (via Visual Crossing API).
*   **Air Raid Alerts:** Near real-time active alerts via the `alerts_in_ua` Python library.
*   **Historical Files:** Ingestion support for historical ISW reports, weather, and alert data from CSV files.

Collected data is structured and stored in a relational database (MySQL on AWS RDS) to create a historical archive for analysis and future model training. The ultimate goal is to develop predictive models capable of forecasting relevant events within a 24-hour timeframe to enhance situational awareness.

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
*   **Basic Infrastructure:**
    *   Modular Python code structure.
    *   Configuration for database and API credentials.
    *   Setup scripts/methods for database table creation and region initialization.
    *   Designed for EC2 deployment with `cron` for scheduling.

### Planned

*   **Advanced Feature Engineering:**
    *   Extracting relevant features from ISW reports (potentially using NLP).
    *   Creating time-based features from weather and alert data.
    *   Combining features across different data sources.
*   **Predictive Modeling:**
    *   Training, evaluating, and tuning machine learning models to predict event likelihood.
    *   Storing and versioning trained models.
*   **Prediction Generation:**
    *   Scheduled task to generate 24-hour forecasts per region.
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
4.  **Forecasting Module (EC2 - Planned):** Will handle feature engineering, model training, and prediction generation.
5.  **Web Application (EC2 - Planned):** Flask backend and basic frontend for user interaction.

*(See `docs/` folder for detailed Architecture, ERD, and Data Flow diagrams)*

## Technology Stack

| Category                | Technologies                                       | Status      |
| :---------------------- | :------------------------------------------------- | :---------- |
| Language                | Python 3.8.0                                       | Implemented |
| Core Libraries          | `pandas`, `datetime`, `json`                       | Implemented |
| Data Acquisition        | `requests`, `re`, `alerts_in_ua`                   | Implemented |
| Database                | AWS RDS (MySQL engine)                             | Implemented |
| DB Connector            | `mysql-connector-python`                           | Implemented |
| Cloud Platform          | AWS (EC2, RDS)                                     | Implemented |
| Scheduling              | `cron` (Linux)                                     | Implemented |
| Version Control         | Git                                                | Implemented |
| **Planned**             |                                                    |             |
| Web Framework           | Flask                                              | Planned     |
| App Server              | uWSGI                                              | Planned     |
| Data Science            | will be decided later                              | Planned     |
| NLP                     | will be decided later                              | Planned     |

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8.0
    *   Git
    *   Access to an AWS account (for deploying EC2/RDS)
    *   MySQL client tools (optional, for direct DB access)

2.  **Clone Repository:**

3.  **Set Up Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate 
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configuration:**
    *   Required variables:
        *   `DB_HOST`: Your AWS RDS endpoint URL
        *   `DB_NAME`: Your database name
        *   `DB_USER`: Your database username
        *   `DB_PASS`: Your database password
        *   `DB_PORT`: Database port (default: 3306)
        *   `WEATHER_API_KEY`: Your API key for the weather service (e.g., Visual Crossing)
        *   `ALERTS_API_TOKEN`: Your API token for the `alerts_in_ua` service

6.  **Database Setup:**
    *   Ensure your RDS instance is running and accessible from where you'll run the scripts (e.g., your EC2 instance).
    *   Run a script or manually use the `DatabaseHandler` class to:
        *   Create the necessary tables:
            ```python
            from src.database.db_handler import DatabaseHandler
            db = DatabaseHandler(**db_config)
            db.connect()
            db.create_tables()
            ```
        *   Initialize the `regions` table with names and coordinates:
            ```python
            # (Connect first as above)
            db.initialize_regions_in_database()
            ```

7.  **Running Collectors Manually (for testing):**
    *   The receive_and_load.ipynb notebook provides detailed information regarding the use of collectors, adding and retrieving information from a database, adding information from files, etc.

8.  **Scheduling with Cron (on EC2):**
    *   Create a main runner script (e.g., `daily_runner.py`) that imports and calls the necessary collector functions for the daily update (e.g., yesterday's ISW, today's weather forecast, active alerts).
    *   Set up a cron job on your EC2 instance to execute this script daily. Example crontab entry 

9.  **Historical Data Ingestion:**
    *   Upload your historical CSV files (or other formats) to the EC2 instance.
    *   Use scripts similar to the examples in the provided Jupyter Notebook (`.ipynb` file) to:
        *   Read the file into a Pandas DataFrame (`pd.read_csv(...)`).
        *   Define the appropriate `region_mapping` and `col_mapping` dictionaries to match your file structure to the database requirements.
        *   Call the relevant `db.insert_..._data()` method.

## Usage

Currently, the primary interaction is through:

1.  **Running Collectors:** Either manually for testing/backfilling or via the scheduled `cron` job for automatic daily updates.
2.  **Database Inspection:** Querying the AWS RDS database directly (using a MySQL client) to view the collected data.

The planned web interface will provide a user-friendly way to explore the data and (eventually) the predictions.

## Future Work

*   Implement Feature Engineering pipeline.
*   Develop and train Machine Learning models for event prediction.
*   Build the Flask backend API.
*   Create the frontend user interface.
*   Implement prediction storage and retrieval.
*   Add comprehensive logging and monitoring.
*   Refine error handling and data validation.
*   Improve handling of duplicate alerts.
