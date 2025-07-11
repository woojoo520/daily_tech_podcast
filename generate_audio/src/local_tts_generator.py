import requests 
from copy import deepcopy
import retrying

DEFAULT_PAYLOAD = {
    "model": "kokoro",
    "input": "",
    "voice": "zm_yunyang",
    "response_format": "mp3",
    "download_format": "mp3",
    "speed": 1,
    "stream": True,
    "return_download_link": False,
    "lang_code": "z",
    "volume_multiplier": 1,
    "normalization_options": {
        "normalize": True,
        "unit_normalization": False,
        "url_normalization": True,
        "email_normalization": True,
        "optional_pluralization_normalization": True,
        "phone_normalization": True,
        "replace_remaining_symbols": True
    }
}

class AudioGenerator:
    def __init__(self, api_url):
        self.api_url = api_url

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=1000)
    def generate_audio_from_text(self, text, filename):
        payload = deepcopy(DEFAULT_PAYLOAD)
        payload['input'] = text
        response = requests.post(self.api_url, json=payload)
        if response.status_code == 200:
            with open(filename, 'wb') as audio_file:
                audio_file.write(response.content)
            return filename
        else:
            raise Exception(f"Error generating audio: {response.status_code} - {response.text}")
        
    def merge_audio_files(self, audio_files, output_filename):
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        one_sec_silence = AudioSegment.silent(duration=500)
        for audio_file in audio_files:
            audio_segment = AudioSegment.from_file(audio_file)
            combined += audio_segment
            combined += one_sec_silence
        combined.export(output_filename, format="mp3")
        return output_filename
    
    def generate_transcript_from_audio(self, audio_file):
        from openai_whisper import Whisper
        whisper = Whisper()
        transcript = whisper.transcribe(audio_file)
        return transcript
        