from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from audio_generator import AudioGenerator
from github_uploader import GitHubUploader
from typing import List
from config import *
from uuid import uuid4

app = FastAPI()
audio_generator = AudioGenerator(API_ENDPOINT)
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


if __name__ == "__main__":
    request = AudioRequest(
        date="2025-07-07",
        text=["今天是2025年7月7日。\n\n明天是2025年7月8日。"]
    )
    generate_audio(request)
    print("Audio generation completed.")