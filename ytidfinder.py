import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()
import os

# Set your API key
api_key = os.getenv("YOUTUBE_API_KEY")


def get_channel_id(channel_username):
    youtube = build("youtube", "v3", developerKey=api_key)

    # Retrieve the channel details
    response = youtube.channels().list(
        part="id",
        forUsername=channel_username,
    ).execute()

    return response.get("items", [])[0]["id"]

if __name__ == "__main__":
    channel_username = "Mrwhosetheboss"
    channel_id = get_channel_id(channel_username)
    print(f"The channel ID for {channel_username} is: {channel_id}")
