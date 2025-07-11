import os 

API_ENDPOINT = "http://localhost:8880/v1/audio/speech" 
GITHUB_REPO = "woojoo520/daily_tech_podcast"  
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") 
MINIMAX_GROUP_ID = os.environ.get("MINIMAX_GROUP_ID", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
AUDIO_FILE_FORMAT = "mp3" 
SAVE_DIRECTORY = "audio_files" 
RSS_FEEDSOURCE = os.environ.get("RSS_FEEDSOURCE", "https://raw.githubusercontent.com/woojoo520/daily_tech_podcast/refs/heads/main/soul_power_tech_news.xml")