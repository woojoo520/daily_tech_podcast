from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# from local_tts_generator import AudioGenerator
# from uuid import uuid4
from github_uploader import GitHubUploader
from config import *
from minimax_generator import generate_audio_from_text
from rss_handler import RSSHandler, PodEpisode
from mutagen.mp3 import MP3
from urllib.parse import urljoin
import time


app = FastAPI()
# audio_generator = AudioGenerator(API_ENDPOINT)
github_helpers = GitHubUploader(GITHUB_TOKEN, GITHUB_REPO)
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

class AudioRequest(BaseModel):
    date: str = "2025-07-07"
    text: str


@app.post("/generate-audio")
def generate_audio(request: AudioRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    filepath = generate_audio_from_text(request.text)
    # filepath = "/Users/woojoo/workspace/daily_tech_podcast/generate_audio/output/output_total_1752204229.mp3"
    
    # upload to GitHub
    audio = MP3(filepath)
    duration_seconds = audio.info.length
    size_bytes = os.path.getsize(filepath)
    audio_path = f"episodes/{request.date}/audio.mp3"
    script_path = f"episodes/{request.date}/script.txt"
    
    github_helpers.upload_file(
        source_filepath=filepath,
        target_filepath=audio_path,
        commit_message=f"Add audio for {request.date}"
    )
    
    github_helpers.upload_contents(
        content=f"{int(duration_seconds)},{size_bytes}\n" + request.text,
        target_filepath=script_path,
        commit_message=f"Add script for {request.date}"
    )
    
    audit_source = urljoin(github_helpers.source_base_path, audio_path)
    script_source = urljoin(github_helpers.source_base_path, script_path)
    
    return {
        "publication_ts": int(time.time()), 
        "audit_source": audit_source, 
        "script_source": script_source, 
        "duration": int(duration_seconds), 
        "filesize": size_bytes
    }


@app.post("/add_new_espisode")
def add_new_episode(episode: PodEpisode):
    rss_handler = RSSHandler(feed_source=RSS_FEEDSOURCE)
    rss_handler.add_new_episodes(episode)
    rss_content = rss_handler.get_rss_str()
    github_helpers.upload_contents(
        content=rss_content,
        target_filepath="soul_power_tech_news.xml",
        commit_message="Update RSS feed with new episode"
    )
    return {"message": "Episode added successfully"}
    

'''
# localhost test 
@app.post("/generate-audio")
def generate_audio(request: AudioRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    try:
        textlist = list(filter(lambda x: x.strip(), request.text.split("\n")))
        # generate seperate audio files
        merged_filepath = f"{SAVE_DIRECTORY}/{request.date}.mp3"
        seperated_files = []
        for text in textlist:
            if not text.strip():
                continue
            cleaned_text = text.strip()
            sep_filepath = f"{SAVE_DIRECTORY}/seperated_{uuid4()}.mp3"
            try:
                audio_generator.generate_audio_from_text(cleaned_text, sep_filepath)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generating audio for text '{cleaned_text}': {str(e)}")
            seperated_files.append(sep_filepath)
        
        if not seperated_files:
            raise HTTPException(status_code=400, detail="No valid audio files generated")
        audio_generator.merge_audio_files(seperated_files, merged_filepath)
        
        # clean seperated files
        for file in seperated_files:
            if os.path.exists(file):
                os.remove(file)
        
        # upload to GitHub
        github_helpers.upload_file(
            source_filepath=merged_filepath,
            target_filepath=f"episodes/{request.date}/audio.mp3",
            commit_message=f"Add audio for {request.date}"
        )
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
'''

# if __name__ == "__main__":
#     request = AudioRequest(
#         date="2025-07-07",
#         text="今天是2025年7月7日。\n\n明天是2025年7月8日。"
#     )
#     generate_audio(request)
#     print("Audio generation completed.")