import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from pymongo import MongoClient
import schedule
import time
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["youtube_summary_app"]
users_collection = db["users"]

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

# YouTube API setup
youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

class User(BaseModel):
    email: str
    channels: list[str]

def send_welcome_email(user_email: str, subscribed_channels: list[str]):
    subject = "Welcome to YouTube Channel Summary Service"
    body = f"Welcome to our YouTube Channel Summary Service!\n\n"
    body += "You have successfully subscribed to the following channels:\n"
    for channel in subscribed_channels:
        body += f"- {channel}\n"
    body += "\nYou will receive weekly summaries of the latest videos from these channels every Monday at 9:00 AM.\n"
    body += "\nThank you for using our service!"

    send_email(user_email, subject, body)

@app.post("/subscribe")
async def subscribe(user: User, background_tasks: BackgroundTasks):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        users_collection.update_one({"email": user.email}, {"$set": {"channels": user.channels}})
        message = "Subscription updated successfully"
    else:
        users_collection.insert_one(user.dict())
        message = "Subscription created successfully"
        # Send welcome email for new users
        background_tasks.add_task(send_welcome_email, user.email, user.channels)

    return {"message": message}

@app.get("/users/{email}")
async def get_user(email: str):
    user = users_collection.find_one({"email": email})
    if user:
        return {"email": user["email"], "channels": user["channels"]}
    raise HTTPException(status_code=404, detail="User not found")

def get_channel_id(channel_name):
    request = youtube.search().list(
        q=channel_name,
        type="channel",
        part="id",
        maxResults=1
    )
    response = request.execute()
    if response["items"]:
        return response["items"][0]["id"]["channelId"]
    return None

def get_latest_video_url(channel_id):
    request = youtube.search().list(
        channelId=channel_id,
        type="video",
        part="id",
        order="date",
        maxResults=1
    )
    response = request.execute()
    if response["items"]:
        return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    return None

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

        return summary

    except YouTubeTranscriptApi.CouldNotRetrieveTranscriptException:
        return "Could not retrieve transcript for this video. Please check if subtitles are available."
    except Exception as e:
        return f"An error occurred: {e}"

def send_email(receiver_email, subject, body):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def weekly_update():
    users = users_collection.find()
    for user in users:
        summaries = []
        for channel_name in user["channels"]:
            channel_id = get_channel_id(channel_name)
            if channel_id:
                video_url = get_latest_video_url(channel_id)
                if video_url:
                    summary = extract_transcript_details_and_generate_gemini_summary(video_url)
                    summaries.append(f"Channel: {channel_name}\nVideo: {video_url}\nSummary: {summary}\n\n")

        if summaries:
            email_body = "Here are your weekly YouTube channel summaries:\n\n" + "\n".join(summaries)
            send_email(user["email"], "Weekly YouTube Channel Summaries", email_body)

@app.on_event("startup")
async def startup_event():
    schedule.every().tuesday.at("22:40").do(weekly_update)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    import threading
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

@app.get("/fetch_channels")
async def fetch_channels(query: str):
    try:
        search_response = youtube.search().list(q=query, type="channel", part="snippet", maxResults=5).execute()
        channels = [
            {"name": item["snippet"]["title"], "id": item["snippet"]["channelId"]}
            for item in search_response["items"]
        ]
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
