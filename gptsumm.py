from langchain.document_loaders import YoutubeLoader
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import os
import time  # Import the time module

# Load environment variables
load_dotenv()

# Replace with your own channel names or URLs
channels_to_follow = ["mkbhd", "freecodecamp", "techwithtim"]

# Set up YouTube API credentials
api_key = os.getenv("YOUTUBE_API_KEY")
API_KEY = api_key
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# Function to get the latest videos from specified channels
def get_latest_videos(api_key, channels):
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=api_key)

    videos = []
    for channel in channels:
        # Get channel ID
        search_response = youtube.search().list(q=channel, type="channel", part="id").execute()
        channel_id = search_response["items"][0]["id"]["channelId"]

        # Get latest videos from the channel
        playlist_response = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        videos_response = youtube.playlistItems().list(playlistId=playlist_id, part="snippet", maxResults=5).execute()
        
        # Add channel information to each video
        for video in videos_response["items"]:
            video["channel"] = channel
            videos.append(video)

    return videos

# Set up OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", api_key=api_key)

# Get videos from the channels (assuming latest_videos is available)
latest_videos = get_latest_videos(API_KEY, channels_to_follow)

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)

# Load and summarize videos
class TextWrapper:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}

texts = []

# for every 30 seconds, it will retrieve one video and then summarize it
for video in latest_videos:
    try:
        # Get video URL, title, and channel information
        video_url = f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}"
        video_title = video['snippet']['title']
        channel_title = video['snippet']['channelTitle']

        # Load video content
        loader = YoutubeLoader.from_youtube_url(video_url, add_video_info=True)
        result = loader.load()

        # Include video title and channel information in the summarization
        text_with_info = f"Video Title: {video_title}\nChannel: {channel_title}\n\n{result}"
        
        # Wrap the text in a simple class to mimic expected structure
        texts.append(TextWrapper(text_with_info, metadata={"video_url": video_url, "video_title": video_title}))
        
    except ValueError as e:
        print(f"Error processing video with URL {video_url}: {e}")  

# Load and run summarization chain if texts list is not empty
if texts:
    # Load and run summarization chain
    print("Texts before summarization:", texts)

    chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=True)

    for text in texts:
        # Summarize the video content
        chain.run([text])

        # Introduce a delay of 30 seconds before summarizing the next video
        time.sleep(30)