import smtplib
import ssl
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import googleapiclient.discovery
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
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
        print("Could not retrieve transcript for this video. Please check if subtitles are available.")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

# Set up email content
subject = "Subject: YouTube Video Summary"
body = "This email contains the summary of a YouTube video generated using Gemini."

# Prompt user to input the YouTube channel they want to summarize
channel_to_follow = input("Enter the YouTube channel you want to summarize: ")

# Fetch latest videos from the specified channel
youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
search_response = youtube.search().list(q=channel_to_follow, type="channel", part="id").execute()
channel_id = search_response["items"][0]["id"]["channelId"]

playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=5).execute()
latest_videos = videos_response["items"]

# Prompt user to select a video index for summarization
for i, video in enumerate(latest_videos):
    print(f"{i+1}. {video['snippet']['title']}")

video_index = int(input("Enter the index of the video you want to summarize (1 to 5): ")) - 1
video = latest_videos[video_index]
video_url = f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}"
video_title = video['snippet']['title']
channel_title = video['snippet']['channelTitle']

# Extract transcript details and generate summary
transcript_text, gemini_summary = extract_transcript_details_and_generate_gemini_summary(video_url)

# Check if transcript and summary are available before proceeding
if transcript_text and gemini_summary:
    # Compose the email body with the transcript and summary
    body += f"\n\nSummary:\n{gemini_summary}"

    # Compose the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    receiver_emails_input = input("Enter recipient email addresses (separated by commas): ")
    receiver_emails = [email.strip() for email in receiver_emails_input.split(',')]

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_emails, message.as_string())
    print(f"Summary of the video using Gemini has been sent to {receiver_emails}.")
else:
    print("Unable to generate summary. Exiting.")
