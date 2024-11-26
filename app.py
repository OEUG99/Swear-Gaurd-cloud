import os
import string
from flask import Flask, request, jsonify
import whisper_timestamped as whisper
import json
from pydub import AudioSegment
from pydub.generators import Sine

# Constants
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
AUDIO_FILE = "test.mp3"
MODEL_SIZE = "tiny"
DEVICE_TYPE = "cpu"
LANGUAGE = "en"
app = Flask(__name__)

def setup_ffmpeg_path(ffmpeg_path):
    os.environ['PATH'] += f':{os.path.dirname(ffmpeg_path)}'


def load_and_transcribe_audio(file_path, model_size, device, language):
    audio = whisper.load_audio(file_path)
    model = whisper.load_model(model_size, device=device)
    return whisper.transcribe(model, audio, language=language)

def beep_swears(audio_path, transcription, swear_list=None):
    if swear_list is None:
        swear_list = [""]  # Default swear words list
    audio = AudioSegment.from_file(audio_path, format="mp3")
    beep = Sine(1000).to_audio_segment(duration=500)
    beeps = []
    for segment in transcription["segments"]:
        for word in segment["words"]:
            if word["text"].lower().strip(string.punctuation) in swear_list:
                print("swear detected:" + word["text"])
                start = word["start"] * 1000
                end = word["end"] * 1000
                beeps.append((start, end))
            else:
                print("no swear detected:" + word["text"])
    output_audio = audio
    for start, end in beeps:
        output_audio = output_audio[:start] + beep[:end-start] + output_audio[end:]
    output_audio.export("censored_output.mp3", format="mp3")

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
    print(json.dumps(transcription_result, indent=2, ensure_ascii=False))
    beep_swears(AUDIO_FILE, transcription_result, swear_list=["line", "example_swear"])


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify(error="No audio file provided"), 400

    audio_file = request.files['audio']
    audio_file.save(AUDIO_FILE)

    transcription_result = load_and_transcribe_audio(AUDIO_FILE, MODEL_SIZE, DEVICE_TYPE, LANGUAGE)
    return jsonify(transcription_result), 200

@app.route('/beep_swears', methods=['POST'])
def beep_swears_audio():
    if 'audio' not in request.files:
        return jsonify(error="No audio file provided"), 400

    audio_file = request.files['audio']
    audio_file.save(AUDIO_FILE)

    swear_list = request.form.get('swear_list')
    if swear_list:
        swear_list = json.loads(swear_list)
    else:
        return jsonify(error="No swear list provided"), 400

    transcription_result = load_and_transcribe_audio(AUDIO_FILE, MODEL_SIZE, DEVICE_TYPE, LANGUAGE)

    beep_swears(AUDIO_FILE, transcription_result, swear_list)

    return jsonify(success=True, message="Censored audio created successfully."), 200

@app.route('/')
def index():
    return "Welcome to the Audio Processing API"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
    #main()