
import smtplib
import os
import logging
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from langchain.llms import OpenAI, Anthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pymongo import MongoClient
import schedule
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI()

# MongoDB setup
try:
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["youtube_summary_app"]
    users_collection = db["users"]
    client.admin.command('ping')
    logging.info("Connected to MongoDB successfully!")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    raise

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

# Configure OpenAI and Anthropic
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# YouTube API setup
youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

class User(BaseModel):
    email: str
    channels: list[str]

def send_email(receiver_email, subject, body):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        logging.info(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {receiver_email}: {e}")

def send_welcome_email(user_email: str, subscribed_channels: list[str]):
    subject = "Welcome to YouTube Channel Summary Service"
    body = f"Welcome to our YouTube Channel Summary Service!\n\n"
    body += "You have successfully subscribed to the following channels:\n"
    for channel in subscribed_channels:
        body += f"- {channel}\n"
    body += "\nYou will receive weekly summaries of the latest videos from these channels every Monday at 9:00 AM.\n"
    body += "\nThank you for using our service!"

    send_email(user_email, subject, body)


@app.get("/")
def read_root():
    return {"Service": "YouTube Channel Summary Service"}

@app.post("/subscribe")
async def subscribe(user: User, background_tasks: BackgroundTasks):
    try:
        existing_user = users_collection.find_one({"email": user.email})
        if existing_user:
            users_collection.update_one({"email": user.email}, {"$set": {"channels": user.channels}})
            message = "Subscription updated successfully"
            logging.info(f"Updated subscription for user: {user.email}")
        else:
            users_collection.insert_one(user.dict())
            message = "Subscription created successfully"
            logging.info(f"Created new subscription for user: {user.email}")
            # Send welcome email for new users
            background_tasks.add_task(send_welcome_email, user.email, user.channels)
            logging.info(f"Scheduled welcome email for user: {user.email}")

        return {"message": message}
    except Exception as e:
        logging.error(f"Error in subscribe endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{email}")
async def get_user(email: str):
    try:
        user = users_collection.find_one({"email": email})
        if user:
            return {"email": user["email"], "channels": user["channels"]}
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logging.error(f"Error in get_user endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_channel_id(channel_name):
    try:
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
    except Exception as e:
        logging.error(f"Error getting channel ID for {channel_name}: {e}")
        return None

def get_latest_video_url(channel_id):
    try:
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
    except Exception as e:
        logging.error(f"Error getting latest video URL for channel {channel_id}: {e}")
        return None

def extract_transcript_details_and_generate_summary(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = " ".join([i["text"] for i in transcript_text])

        # Try Gemini first
        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"You are YouTube video summarizer. Please provide the important summary of the video transcript:\n\n{transcript}"
            response = model.generate_content(prompt)
            return response.text
        except Exception as gemini_error:
            logging.error(f"Gemini error: {gemini_error}")

        # If Gemini fails, try OpenAI
        try:
            llm = OpenAI(api_key=openai_api_key)
            prompt = PromptTemplate(
                input_variables=["transcript"],
                template="Summarize the following YouTube video transcript:\n\n{transcript}"
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            return chain.run(transcript=transcript)
        except Exception as openai_error:
            logging.error(f"OpenAI error: {openai_error}")

        # If OpenAI fails, try Anthropic
        try:
            llm = Anthropic(api_key=anthropic_api_key)
            prompt = PromptTemplate(
                input_variables=["transcript"],
                template="Summarize the following YouTube video transcript:\n\n{transcript}"
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            return chain.run(transcript=transcript)
        except Exception as anthropic_error:
            logging.error(f"Anthropic error: {anthropic_error}")

        # If all methods fail, return an error message
        return "Unable to generate summary due to API issues. Please try again later."

    except Exception as e:
        logging.error(f"Error in extract_transcript_details_and_generate_summary: {e}")
        return f"An error occurred: {e}"

def weekly_update():
    logging.info("Starting weekly update")
    users = users_collection.find()
    for user in users:
        summaries = []
        for channel_name in user["channels"]:
            channel_id = get_channel_id(channel_name)
            if channel_id:
                video_url = get_latest_video_url(channel_id)
                if video_url:
                    summary = extract_transcript_details_and_generate_summary(video_url)
                    summaries.append(f"Channel: {channel_name}\nVideo: {video_url}\nSummary: {summary}\n\n")

        if summaries:
            email_body = "Here are your weekly YouTube channel summaries:\n\n" + "\n".join(summaries)
            send_email(user["email"], "Weekly YouTube Channel Summaries", email_body)
            logging.info(f"Sent weekly summary to {user['email']}")
    logging.info("Completed weekly update")

@app.on_event("startup")
async def startup_event():
    schedule.every().wednesday.at("09:44").do(weekly_update)
    logging.info("Scheduled weekly update for Mondays at 09:00")

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logging.info("Started scheduler thread")

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
        logging.error(f"Error in fetch_channels endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    logging.info("Starting the FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)