import nest_asyncio
import os
import csv
import re
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
from scripts.logging import logger

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables from .env file
load_dotenv('.env')
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

# Initialize the Telegram client
client = TelegramClient('scraping_session', api_id, api_hash)

# Define the CSV file to store the data
csv_file = 'telegram_data.csv'

def write_to_csv(message_date, message_id, message_text):
    """Append a message to the CSV file."""
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            message_date, 
            message_id,
            message_text.strip(),
        ])

# Function to scrape messages from Telegram channels
async def scrape_telegram_channels(channels):
    """
    Scrapes historical messages from a Telegram channel and saves the data to a CSV file.
    Args:
    channels : List of Telegram channel usernames to scrape.
    """
    media_dir = os.path.join('yolov5', 'data', 'images')
    os.makedirs(media_dir, exist_ok=True)

    # Start the client once, no need to call it again
    await client.start() 
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['message_date', 'message_id', 'message_description'])  # Write CSV header

    for channel_username in channels:
        entity = await client.get_entity(channel_username)
        channel_title = entity.title
        print(f"Scraping historical data from {channel_username} ({channel_title})...")

        async for message in client.iter_messages(entity, limit=30):
            if message.message:
                text_reg = r'[\u1200-\u137F0-9a-zA-Z\+\-_\.\:/\?\&=%]+'
                url_reg = r'http[s]?://\S+|www\.\S+'
                
                mess_text = ' '.join(re.findall(text_reg, message.message))
                mess_text = re.sub(url_reg, '', mess_text)

                if mess_text.strip(): 
                    message_date = message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else '[No Date]'
                    sender_id = message.sender_id if message.sender_id else '[No Sender ID]'
                    write_to_csv(message_date, message.id, mess_text)
            
        logger.info(f"Finished scraping {channel_username}")

    logger.info("Finished scraping all channels.")
    print("Finished scraping all channels.")
    await client.run_until_disconnected()

# Real-time message handler to update the CSV file when new messages arrive
@client.on(events.NewMessage())
async def real_time_message_handler(event):
    message = event.message.message
    if message:
        text_reg = r'[\u1200-\u137F0-9a-zA-Z\+\-_\.\:/\?\&=%]+'
        url_reg = r'http[s]?://\S+|www\.\S+'
        
        mess_text = ' '.join(re.findall(text_reg, message.message))
        mess_text = re.sub(url_reg, '', mess_text)
        
        if mess_text.strip():
            message_date = event.message.date.strftime('%Y-%m-%d %H:%M:%S')
            sender_id = event.message.sender_id if event.message.sender_id else '[No Sender ID]'
            write_to_csv(message_date, event.message.id, mess_text)
            logger.info(f"New message added to CSV: {mess_text}")

async def start_scraping(channels):
    """Start scraping and handle authentication errors"""
    logger.info("Starting scraping...")

    try:
        await client.start()  # Start the client, handle authentication
    except SessionPasswordNeededError:
        # This happens when a password is required (2FA enabled)
        await client.start(password="Your2FAPassword")  # Replace with your actual password

    await scrape_telegram_channels(channels)  # Start scraping historical messages

# Main function to call the start_scraping coroutine
def main(channels):
    # Create an event loop and run the start_scraping coroutine
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_scraping(channels))

# Entry point to run the main script
if __name__ == "__main__":
    # List the channels to scrape dynamically when running the script
    channels = ['@DoctorsET', '@lobelia4cosmetics', '@yetenaweg', '@EAHCI', '@CheMed123']  # Replace this with your dynamic list of channels
    main(channels)
