import os
import string

import whisper_timestamped as whisper
import json

# Constants
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
AUDIO_FILE = "test.mp3"
MODEL_SIZE = "tiny"
DEVICE_TYPE = "cpu"
LANGUAGE = "en"


def setup_ffmpeg_path(ffmpeg_path):
    os.environ['PATH'] += f':{os.path.dirname(ffmpeg_path)}'


def load_and_transcribe_audio(file_path, model_size, device, language):
    audio = whisper.load_audio(file_path)
    model = whisper.load_model(model_size, device=device)
    return whisper.transcribe(model, audio, language=language)

def beep_swears(audio, transcription, swear_list=None):
    if swear_list is None:
        swear_list = ["code"]  # Default swear words list


    transcribed_words = transcription["segments"][0]["words"]
    print(transcribed_words)

    for word in transcribed_words:
        if word["text"].lower().strip(string.punctuation) in swear_list:
            print("swear detected:" + word["text"])
        else:
            print("no swear detected:" + word["text"])


def main():
    setup_ffmpeg_path(FFMPEG_PATH)
    transcription_result = load_and_transcribe_audio(AUDIO_FILE, MODEL_SIZE, DEVICE_TYPE, LANGUAGE)
    #print(json.dumps(transcription_result, indent=2, ensure_ascii=False))
    beep_swears(AUDIO_FILE, transcription_result)


if __name__ == "__main__":
    main()