import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()
import os

# Set your API key
api_key = os.getenv("YOUTUBE_API_KEY")


# Set the YouTube channels you want to follow
channels = ["UCBJycsmduvYEL83R_U4JriQ", "UCMiJRAwDNSNzuYeN2uWa0pA"]

def get_latest_videos(channel_id):
    youtube = build("youtube", "v3", developerKey=api_key)

    # Retrieve the latest videos from the channel
    response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        type="video",
    ).execute()

    return response.get("items", [])

def main():
    for channel_id in channels:
        videos = get_latest_videos(channel_id)
        print(f"Latest videos for channel {channel_id}:")
        for video in videos:
            print(f"Title: {video['snippet']['title']}")
            print(f"Video ID: {video['id']['videoId']}")
            print("\n")

if __name__ == "__main__":
    main()
