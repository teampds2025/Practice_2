import asyncio
import os
import json
import pytz
from datetime import datetime, timedelta
from telethon import TelegramClient
import pandas as pd

class TelegramFetcher:
    """
    A class to fetch messages from a Telegram chat within a specified date range.
    """
    def __init__(self, api_id, api_hash, session_name, output_dir='telegram_data'):
        """
        Initializes the TelegramFetcher.
        """
        self.output_dir = output_dir
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)


    async def connect(self):
        await self.client.connect()

        if not await self.client.is_user_authorized():
            phone = input("Enter your phone number: ").strip()
            await self.client.send_code_request(phone)
            code = input("Enter the code you received: ").strip()
            await self.client.sign_in(phone, code)

        print("Connected")

    async def disconnect(self):
        if self.client.is_connected():
            await self.client.disconnect()
            print("Disconnected.")

    async def fetch_messages(self, chat_id, limit=None, start_date=None, end_date=None):
        """
        Fetches messages from a chat within a specified date range using the initialized client.
        """

        kyiv_tz = pytz.timezone('Europe/Kyiv')

        if not self.client.is_connected():
            await self.connect()

        if not start_date or not end_date:
            print(" Start date and end date are required.")
            return []

        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(kyiv_tz) - timedelta(hours=3)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999).astimezone(kyiv_tz) - timedelta(hours=3)

        print(f"Fetching messages from chat: {chat_id}")
        print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        messages_data = []
        message_count = 0


        async for message in self.client.iter_messages(
                chat_id,
                limit=None,  # manual limit applied later
                reverse=False, # fetch newest first, going back in time
                offset_date=end_date # from messages at or before the end_date
        ):

            if message.date < start_date:
                print("Reached start date boundary.")
                break

            # check is necessary even with offset_date because iter_messages goes backwards
            if start_date <= message.date <= end_date:
                if message.text is None:
                    continue

                kyiv_date = message.date.astimezone(kyiv_tz)

                messages_data.append({
                    'date': kyiv_date.isoformat(),
                    'message': '' if message.text is None else message.text
                })
                message_count += 1

                if limit is not None and message_count >= limit:
                    print(f"Reached specified limit of {limit} messages within date range.")
                    break

        messages_data.sort(key=lambda m: m['date'])
        print(f"Finished fetching. Found {len(messages_data)} messages within the date range.")
        return messages_data

    async def save_messages_to_csv(self, messages, filename="messages.csv"):
      """
      Converts fetched messages to a pandas DataFrame and saves it to a CSV file.
      """
      if not messages:
        print("No messages provided to save to CSV.")
        return

      os.makedirs(self.output_dir, exist_ok=True)
      filepath = os.path.join(self.output_dir, filename)
      df = pd.DataFrame(messages)
      df.to_csv(filepath, index=False)
      print(f"Successfully converted {len(messages)} messages to DataFrame and saved to {filepath}")