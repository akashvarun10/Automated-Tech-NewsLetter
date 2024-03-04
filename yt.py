import os
import time
import google.oauth2.credentials
from googleapiclient.discovery import build
import smtplib
from email.mime.text import MIMEText

import os 
from dotenv import load_dotenv
load_dotenv()

# YouTube API Key
API_KEY = os.getenv("YOUTUBE_API_KEY")

# YouTube Usernames
usernames = ['freecodecamp', 'TechWithTim', 'Deeplearningai']

# Email configuration
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
receiver_email = 'akashvarunp@gmail.com'

# Function to get Channel ID based on username
def get_channel_id(username):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.channels().list(
        part='id',
        forUsername=username
    )
    response = request.execute()
    
    items = response.get('items', [])
    if items:
        channel_id = items[0]['id']
        return channel_id
    else:
        print(f"Unable to find Channel ID for username: {username}")
        return None

# Function to get video details
def get_new_videos(channel_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        order='date',
        type='video',
        maxResults=5  # Adjust as needed
    )
    response = request.execute()
    videos = []
    for item in response.get('items', []):
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        videos.append({'id': video_id, 'title': video_title})
    return videos

# Function to send email
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Main loop
while True:
    for username in usernames:
        channel_id = get_channel_id(username)
        videos = get_new_videos(channel_id)
        if videos:
            subject = f"New Videos Uploaded on Channel {username}"
            body = "\n".join([f"{video['title']} - https://www.youtube.com/watch?v={video['id']}" for video in videos])
            send_email(subject, body)

    # Adjust the sleep time as needed
    time.sleep(3600)  # Check every hour
