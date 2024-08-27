# import smtplib
# import os
# from dotenv import load_dotenv
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import googleapiclient.discovery
# from youtube_transcript_api import YouTubeTranscriptApi
# import google.generativeai as genai  # Add this line
# import schedule
# import time

# load_dotenv()

# # Set up email credentials for Outlook
# smtp_server = os.getenv("SMTP_SERVER")
# port = 587  # For STARTTLS
# sender_email = os.getenv("SENDER_EMAIL")
# password = os.getenv("SENDER_PASSWORD")

# # Set up YouTube API credentials
# API_KEY = os.getenv("YOUTUBE_API_KEY")
# API_SERVICE_NAME = "youtube"
# API_VERSION = "v3"

# # Configure Google API for Gemini
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # Set up email content
# subject = "Subject: Daily Newsletter - Uploaded Videos"
# body = "This email contains the summary of uploaded videos from the selected channels."


# # Function to extract transcript details and generate summaries using Gemini
# def extract_transcript_details_and_generate_gemini_summary(youtube_video_url):
#     try:
#         video_id = youtube_video_url.split("=")[1]
#         transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

#         transcript = ""
#         for i in transcript_text:
#             transcript += " " + i["text"]

#         # Use Gemini to generate summary
#         model = genai.GenerativeModel("gemini-pro")
#         prompt = f"You are YouTube video summarizer. Please provide the important summary of the video transcript:\n\n"
#         response = model.generate_content(prompt + transcript)
#         summary = response.text

#         return transcript, summary

#     except YouTubeTranscriptApi.CouldNotRetrieveTranscriptException:
#         return None, None
#     except Exception as e:
#         raise Exception(f"An error occurred: {e}")


# # Function to fetch latest videos from a given channel
# def fetch_latest_videos(channel_id):
#     youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
#     playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
#     playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
#     videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=5).execute()
#     return videos_response["items"]


# # Function to send email
# def send_email(receiver_email, email_body):
#     message = MIMEMultipart()
#     message["From"] = sender_email
#     message["To"] = receiver_email
#     message["Subject"] = subject
#     message.attach(MIMEText(email_body, "plain"))

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls()
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message.as_string())


# # Scheduled job to fetch videos and send email
# def schedule_job():
#     # Get list of channels from environment variable
#     channels_to_follow = os.getenv("CHANNELS_TO_FOLLOW").split(',')

#     # Initialize email body
#     email_body = body + "\n\n"

#     for channel in channels_to_follow:
#         try:
#             # Fetch latest videos from the channel
#             videos = fetch_latest_videos(channel)

#             # Add videos to email body
#             email_body += f"Videos from channel: {channel}\n"
#             for idx, video in enumerate(videos, start=1):
#                 video_title = video['snippet']['title']
#                 video_url = f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}"
#                 email_body += f"{idx}. {video_title}\n{video_url}\n\n"

#         except Exception as e:
#             print(f"An error occurred while fetching videos for channel {channel}: {e}")

#     # Send email to the recipients
#     receiver_emails = os.getenv("RECEIVER_EMAILS").split(',')
#     for receiver_email in receiver_emails:
#         try:
#             send_email(receiver_email, email_body)
#             print(f"Email sent to {receiver_email}")
#         except Exception as e:
#             print(f"An error occurred while sending email to {receiver_email}: {e}")


# # Schedule the job to run hourly
# schedule.every().hour.do(schedule_job)


# # Run the scheduler
# while True:
#     schedule.run_pending()
#     time.sleep(1)








import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import streamlit as st
from datetime import datetime, timedelta, timezone

load_dotenv()

# Set up email credentials for Outlook
smtp_server = os.getenv("SMTP_SERVER")
port = 587  # For STARTTLS
sender_email = os.getenv("SENDER_EMAIL")
password = os.getenv("SENDER_PASSWORD")

# Set up YouTube API credentials
API_KEY = os.getenv("YOUTUBE_API_KEY")
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# Configure Google API for Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up email content
subject = "Subject: YouTube Video Summary"
body = "This email contains the summary of YouTube videos uploaded this week.\n\n"

# Function to extract transcript details and generate summaries using Gemini
def extract_transcript_details_and_generate_gemini_summary(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]

        # Use Gemini to generate summary
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"You are YouTube video summarizer. Please provide the important summary of the video transcript:\n\n"
        response = model.generate_content(prompt + transcript)
        summary = response.text

        return transcript, summary

    except YouTubeTranscriptApi.CouldNotRetrieveTranscriptException:
        st.error("Could not retrieve transcript for this video. Please check if subtitles are available.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

@st.cache
def fetch_videos(channel_to_follow):
    try:
        # Fetch latest videos from the specified channel
        youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
        search_response = youtube.search().list(q=channel_to_follow, type="channel", part="id").execute()
        channel_id = search_response["items"][0]["id"]["channelId"]

        playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=5).execute()
        latest_videos = videos_response["items"]

        # Extract video details
        videos_info = []
        for idx, video in enumerate(latest_videos, start=1):
            video_id = video["snippet"]["resourceId"]["videoId"]
            video_response = youtube.videos().list(id=video_id, part="snippet").execute()
            video_published_at = video_response["items"][0]["snippet"]["publishedAt"]
            video_info = {
                "index": idx,
                "title": video['snippet']['title'],
                "channel_title": video['snippet']['channelTitle'],
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "published_at": video_published_at
            }
            videos_info.append(video_info)

        return videos_info

    except Exception as e:
        st.error(f"An error occurred: {e}")

def send_weekly_email(subscribed_channels, receiver_emails):
    try:
        # Get today's date
        today = datetime.now(timezone.utc)

        # Get the start and end dates of the current week (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Set up email content
        subject = "Subject: Weekly YouTube Video Summary"
        body = "This email contains the summary of YouTube videos uploaded this week.\n\n"

        # Compose the email body with the videos
        for channel in subscribed_channels:
            body += f"Videos from channel '{channel}':\n"
            videos = fetch_videos(channel)
            for video in videos:
                video_published_at = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                if start_of_week <= video_published_at <= end_of_week:
                    body += f"- Title: {video['title']}\n  Channel: {video['channel_title']}\n  URL: {video['video_url']}\n\n"

        # Compose the email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_emails
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_emails.split(','), message.as_string())

        st.success(f"Weekly newsletter with video summaries has been sent to {receiver_emails}.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

st.title("YouTube Video Summary Generator")

# Get user input for subscribed channels
subscribed_channels = st.text_input("Enter YouTube channels you are subscribed to (comma-separated):")

# Get user input for receiver emails
receiver_email_input = st.text_input("Enter your email address for receiving weekly newsletters:")

if st.button("Subscribe"):
    subscribed_channels = subscribed_channels.split(',')
    send_weekly_email(subscribed_channels, receiver_email_input)















# import smtplib
# import os
# from dotenv import load_dotenv
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import googleapiclient.discovery
# from youtube_transcript_api import YouTubeTranscriptApi
# import google.generativeai as genai
# import schedule
# import time

# load_dotenv()

# # Set up email credentials for Outlook
# smtp_server = os.getenv("SMTP_SERVER")
# port = 587  # For STARTTLS
# sender_email = os.getenv("SENDER_EMAIL")
# password = os.getenv("SENDER_PASSWORD")

# # Set up YouTube API credentials
# API_KEY = os.getenv("YOUTUBE_API_KEY")
# API_SERVICE_NAME = "youtube"
# API_VERSION = "v3"

# # Configure Google API for Gemini
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # Set up email content
# subject = "Subject: Daily Newsletter - Uploaded Videos"
# body = "This email contains the summary of uploaded videos from the selected channels."


# # Function to extract transcript details and generate summaries using Gemini
# def extract_transcript_details_and_generate_gemini_summary(youtube_video_url):
#     try:
#         video_id = youtube_video_url.split("=")[1]
#         transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

#         transcript = ""
#         for i in transcript_text:
#             transcript += " " + i["text"]

#         # Use Gemini to generate summary
#         model = genai.GenerativeModel("gemini-pro")
#         prompt = f"You are YouTube video summarizer. Please provide the important summary of the video transcript:\n\n"
#         response = model.generate_content(prompt + transcript)
#         summary = response.text

#         return transcript, summary

#     except YouTubeTranscriptApi.CouldNotRetrieveTranscriptException:
#         return None, None
#     except Exception as e:
#         raise Exception(f"An error occurred: {e}")


# # Function to fetch latest videos from a given channel
# def fetch_latest_videos(channel_id):
#     youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
#     playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
#     playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
#     videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=1).execute()
#     return videos_response["items"]


# # Function to send email
# def send_email(receiver_email, email_body):
#     message = MIMEMultipart()
#     message["From"] = sender_email
#     message["To"] = receiver_email
#     message["Subject"] = subject
#     message.attach(MIMEText(email_body, "plain"))

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls()
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message.as_string())


# # Scheduled job to fetch videos and send email
# def schedule_job():
#     # Get list of channels from environment variable
#     channels_to_follow = os.getenv("CHANNELS_TO_FOLLOW").split(',')

#     # Initialize email body
#     email_body = body + "\n\n"

#     for channel in channels_to_follow:
#         try:
#             # Fetch latest video from the channel
#             videos = fetch_latest_videos(channel)

#             if videos:
#                 video = videos[0]
#                 video_title = video['snippet']['title']
#                 video_url = f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}"
#                 transcript_text, gemini_summary = extract_transcript_details_and_generate_gemini_summary(video_url)

#                 if transcript_text and gemini_summary:
#                     # Add video summary to email body
#                     email_body += f"Videos from channel: {channel}\n"
#                     email_body += f"{video_title}\n{video_url}\nSummary:\n{gemini_summary}\n\n"
#         except Exception as e:
#             print(f"An error occurred while processing channel {channel}: {e}")

#     # Send email to the recipients
#     receiver_emails = os.getenv("RECEIVER_EMAILS").split(',')
#     for receiver_email in receiver_emails:
#         try:
#             send_email(receiver_email, email_body)
#             print(f"Email sent to {receiver_email}")
#         except Exception as e:
#             print(f"An error occurred while sending email to {receiver_email}: {e}")


# # Schedule the job to run hourly
# schedule.every().hour.do(schedule_job)


# # Run the scheduler
# while True:
#     schedule.run_pending()
#     time.sleep(1)
