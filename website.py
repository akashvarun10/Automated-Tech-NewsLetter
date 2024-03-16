import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import streamlit as st

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
body = "This email contains the summary of a YouTube video generated using Gemini."

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
            video_info = {
                "index": idx,
                "title": video['snippet']['title'],
                "channel_title": video['snippet']['channelTitle'],
            }
            videos_info.append(video_info)

        return videos_info

    except Exception as e:
        st.error(f"An error occurred: {e}")

def send_summary(video_index, receiver_emails):
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
        selected_video = latest_videos[video_index - 1]
        video_url = f"https://www.youtube.com/watch?v={selected_video['snippet']['resourceId']['videoId']}"
        video_title = selected_video['snippet']['title']
        channel_title = selected_video['snippet']['channelTitle']

        # Extract transcript details and generate summary
        transcript_text, gemini_summary = extract_transcript_details_and_generate_gemini_summary(video_url)

        # Check if transcript and summary are available before proceeding
        if transcript_text and gemini_summary:
            # Compose the email body with the transcript and summary
            email_body = f"{body}\n\nSummary:\n{gemini_summary}"

            # Compose the email
            message = MIMEMultipart()
            message["From"] = sender_email
            message["Subject"] = subject
            message.attach(MIMEText(email_body, "plain"))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_emails.split(','), message.as_string())

            st.success(f"Summary of the video using Gemini has been sent to {receiver_emails}.")
        else:
            st.error("Unable to generate summary. Exiting.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

st.title("YouTube Video Summary Generator")

channel_to_follow = st.text_input("Enter the YouTube channel name to follow:")

if st.button("Fetch Videos"):
    videos = fetch_videos(channel_to_follow)
    if videos:
        st.write("Latest videos from the specified channel:")
        for video in videos:
            st.write(f"Index: {video['index']}, Title: {video['title']}, Channel: {video['channel_title']}")
    else:
        st.error("Failed to fetch videos.")

video_index = st.number_input("Enter the index of the video you want to summarize:", min_value=1, max_value=5, value=1)
receiver_emails = st.text_input("Enter receiver email(s) separated by comma:")

if st.button("Send Summary"):
    send_summary(video_index, receiver_emails)
