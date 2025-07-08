import os 

API_ENDPOINT = "http://localhost:8880/v1/audio/speech" 
GITHUB_REPO = "woojoo520/daily_tech_podcast"  
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") 
AUDIO_FILE_FORMAT = "mp3" 
SAVE_DIRECTORY = "audio_files" 