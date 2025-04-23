import requests
import re
import pandas as pd
from datetime import datetime, timedelta
import time


class ISWDataCollector:
    def __init__(self, base_url="https://www.understandingwar.org/backgrounder/"):
        """
        Initialize the ISWDataCollector with a base URL.
        """

        self.base_url = base_url

    @staticmethod
    def extract_text(html):
        """
        Extracts text content from the first <div> element that contains the given class name.

        Args:
            html (str): The HTML content.

        Returns:
            str or None: The extracted text with HTML tags removed, or None if not found.
        """

        pattern = r'<div[^>]*class\s*=\s*["\'][^"\']*?\bfield-name-body\b[^"\']*?["\'][^>]*?>(.*?\[1\].*?\[1\])'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1)
            text = re.sub(r'<[^>]+>', '', content)
            text = ' '.join(text.split())
            return text.strip()
        return None

    def collect_data(self, start_date, end_date):
        """
        Collects ISW reports from start_date to end_date.

        Args:
            start_date (datetime): Starting date for collection.
            end_date (datetime): Ending date for collection.

        Returns:
            DataFrame: Contains 'date', 'report_text', and 'url' columns with collected data.
        """

        data = []
        current_date = start_date

        while current_date <= end_date:
            day_without_leading_zero = str(current_date.day)
            month_name_lower = current_date.strftime("%B").lower()

            if current_date.year == 2022 and current_date.month == 2:
                if current_date.day == 24:
                    url = f"{self.base_url}russia-ukraine-warning-update-initial-russian-offensive-campaign-assessment"
                elif current_date.day == 25:
                    url = f"{self.base_url}russia-ukraine-warning-update-russian-offensive-campaign-assessment-february-25-2022"
                elif current_date.day == 26:
                    url = f"{self.base_url}russia-ukraine-warning-update-russian-offensive-campaign-assessment-february-26"
                elif current_date.day == 27:
                    url = f"{self.base_url}russia-ukraine-warning-update-russian-offensive-campaign-assessment-february-27"
                elif current_date.day == 28:
                    url = f"{self.base_url}russian-offensive-campaign-assessment-february-28-2022"

            elif current_date.year == 2022 and current_date.month >= 3 and current_date.day >= 1:
                date_str = f"{month_name_lower}-{day_without_leading_zero}"
                url = f"{self.base_url}russian-offensive-campaign-assessment-{date_str}"
            else:
                date_str = f"{month_name_lower}-{day_without_leading_zero}-{current_date.year}"
                url = f"{self.base_url}russian-offensive-campaign-assessment-{date_str}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    report_text = self.extract_text(response.text)
                    if report_text:
                        data.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'report_text': report_text,
                            'url': url
                        })
                        print(f"Successfully collected report for {current_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"Could not find content for {current_date.strftime('%Y-%m-%d')}")
                        break

            except Exception as e:
                print(f"Error collecting data for {current_date.strftime('%Y-%m-%d')}: {str(e)}")
                break

            time.sleep(1)
            current_date += timedelta(days=1)

        df = pd.DataFrame(data)
        return df