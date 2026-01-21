import os
import time
import struct
import tempfile
from google import genai
from google.genai import types
from pydub import AudioSegment
from config import GEMINI_API_KEY


current_dir = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(os.path.dirname(current_dir), "output")


def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    """Parses bits per sample and rate from an audio MIME type string."""
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file from raw audio data."""
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data


def call_gemini_tts(text: str) -> bytes:
    """Call Gemini TTS API and return audio data as WAV bytes."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    model = "gemini-2.5-pro-preview-tts"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Read aloud in a warm and friendly tone: \n{text}"),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Zephyr"
                )
            )
        ),
    )

    audio_chunks = []
    mime_type = None

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue

        part = chunk.candidates[0].content.parts[0]
        if part.inline_data and part.inline_data.data:
            inline_data = part.inline_data
            if mime_type is None:
                mime_type = inline_data.mime_type
            audio_chunks.append(inline_data.data)

    if not audio_chunks:
        raise Exception("No audio data received from Gemini TTS API")

    combined_audio = b"".join(audio_chunks)
    wav_data = convert_to_wav(combined_audio, mime_type or "audio/L16;rate=24000")
    return wav_data


def generate_audio_from_text(text: str, filename: str = "", file_format='mp3') -> str:
    """
    Generate audio from text using Gemini TTS API.

    Args:
        text (str): The text to convert to audio.
        filename (str): The output file name. If empty, use default naming.
        file_format (str): The format of the audio file, default is 'mp3'.

    Returns:
        str: The path to the generated audio file.
    """
    wav_data = call_gemini_tts(text)

    # Determine output file path
    if filename:
        _, ext = os.path.splitext(filename)
        if not ext:
            file_name = os.path.join(output_folder, f"{filename}.{file_format}")
        else:
            file_name = os.path.join(output_folder, filename)
    else:
        timestamp = int(time.time())
        file_name = os.path.join(output_folder, f'output_total_{timestamp}.{file_format}')

    # Convert WAV to MP3 using pydub
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        tmp_wav.write(wav_data)
        tmp_wav_path = tmp_wav.name

    try:
        audio_segment = AudioSegment.from_wav(tmp_wav_path)
        audio_segment.export(file_name, format="mp3", bitrate="128k")
    finally:
        os.unlink(tmp_wav_path)

    return file_name


if __name__ == "__main__":
    text = "今天是2026年1月13日，欢迎您与我们一起开启新的一天。"
    filepath = generate_audio_from_text(text)
    print(f"filepath: {filepath}")
