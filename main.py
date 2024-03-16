# import smtplib
# import ssl
# import os
# from dotenv import load_dotenv
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from fastapi import FastAPI, HTTPException, Query
# import googleapiclient.discovery
# from youtube_transcript_api import YouTubeTranscriptApi
# import google.generativeai as genai  # Add this line

# load_dotenv()

# app = FastAPI()

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
#         raise HTTPException(status_code=400, detail="Could not retrieve transcript for this video. Please check if subtitles are available.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# # Set up email content
# subject = "Subject: YouTube Video Summary"
# body = "This email contains the summary of a YouTube video generated using Gemini."

# @app.post("/send_summary")
# async def send_summary(
#     channel_to_follow: str,
#     video_index: int = Query(..., ge=1, le=5),
#     receiver_emails: str = Query(...),
# ):
#     # Fetch latest videos from the specified channel
#     youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
#     search_response = youtube.search().list(q=channel_to_follow, type="channel", part="id").execute()
#     channel_id = search_response["items"][0]["id"]["channelId"]

#     playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
#     playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

#     videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=5).execute()
#     latest_videos = videos_response["items"]

#     # Extract video details
#     video = latest_videos[video_index - 1]
#     video_url = f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}"
#     video_title = video['snippet']['title']
#     channel_title = video['snippet']['channelTitle']

#     # Extract transcript details and generate summary
#     transcript_text, gemini_summary = extract_transcript_details_and_generate_gemini_summary(video_url)

#     # Check if transcript and summary are available before proceeding
#     if transcript_text and gemini_summary:
#         # Compose the email body with the transcript and summary
#         email_body = f"{body}\n\nSummary:\n{gemini_summary}"

#         # Compose the email
#         message = MIMEMultipart()
#         message["From"] = sender_email
#         message["Subject"] = subject
#         message.attach(MIMEText(email_body, "plain"))

#         # Connect to the SMTP server and send the email
#         with smtplib.SMTP(smtp_server, port) as server:
#             server.starttls()
#             server.login(sender_email, password)
#             server.sendmail(sender_email, receiver_emails.split(','), message.as_string())
        
#         return {"message": f"Summary of the video using Gemini has been sent to {receiver_emails}."}
#     else:
#         raise HTTPException(status_code=500, detail="Unable to generate summary. Exiting.")






import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, Query
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai  # Add this line

load_dotenv()

app = FastAPI()

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
        raise HTTPException(status_code=400,
                            detail="Could not retrieve transcript for this video. Please check if subtitles are available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/fetch_videos")
async def fetch_videos(channel_to_follow: str):
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
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/send_summary")
async def send_summary(
        channel_to_follow: str,
        video_index: int = Query(..., ge=1, le=5),
        receiver_emails: str = Query(...),
):
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

            return {"message": f"Summary of the video using Gemini has been sent to {receiver_emails}."}
        else:
            raise HTTPException(status_code=500, detail="Unable to generate summary. Exiting.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

