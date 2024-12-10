import os
import string
import whisper_timestamped as whisper
from numba.core.ir import Raise

from pydub import AudioSegment
from pydub.generators import Sine
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip

MODEL_SIZE = "tiny"
DEVICE_TYPE = "cpu"
LANGUAGE = "en"
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
os.environ['PATH'] += f':{os.path.dirname(FFMPEG_PATH)}'


def load_and_transcribe_audio(file_path, model_size, device, language):
    audio = whisper.load_audio(file_path)
    model = whisper.load_model(model_size, device=device)
    return whisper.transcribe(model, audio, language=language)


def beep_swears(audio_path, file_id, transcription, swear_list=None):
    if swear_list is None:
        swear_list = ["censor"]  # Replace with a more comprehensive  list later.

    audio = AudioSegment.from_file(audio_path, format="mp3")
    beeps = []

    for segment in transcription["segments"]:
        for word in segment["words"]:
            if "*" in word["text"]:
                print(f"Swear detected: {word['text']}")
                start = max(0, int(word["start"] * 1000))
                end = min(len(audio), int(word["end"] * 1000))
                beeps.append((start, end))
                continue
            if word["text"].lower().strip(string.punctuation) in swear_list:
                print(f"Swear detected: {word['text']}")
                start = max(0, int(word["start"] * 1000))
                end = min(len(audio), int(word["end"] * 1000))
                beeps.append((start, end))
            else:
                print(f"No swear detected: {word['text']}")

    output_audio = audio
    for start, end in beeps:
        duration = end - start
        print(f"Adding beep at {start} ms for {duration} ms")
        beep = Sine(1000).to_audio_segment(duration=duration)  # Match beep duration to censored segment
        output_audio = output_audio[:start] + beep + output_audio[end:]

    print(f"Original audio length: {len(audio)} ms")
    print(f"Censored audio length: {len(output_audio)} ms")
    output_audio.export(file_id+"-censored.mp3", format="mp3")
    print("Censored audio saved as " + file_id+"-censored.mp3")


def extract_audio_from_video(video_path, extracted_audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(extracted_audio_path, codec="mp3")
    if os.path.exists(extracted_audio_path):
        print(f"Extracted audio saved as '{extracted_audio_path}'.")
    else:
        print("Failed to extract audio.")

def replace_audio_in_video(video_path, censored_audio_path, output_video_path):
    # Load the video without its original audio
    video = VideoFileClip(video_path)


    # Creating composite audio
    beeped_audio = CompositeAudioClip([AudioFileClip(censored_audio_path)])

    video.audio = beeped_audio

    video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

    print(f"Replaced audio in the video saved as '{output_video_path}'.")

def process_video(video_path, file_id, swear_list=None):

    # Step 1: Extract audio from video to generate a stand alone mp3 at the extracted audio path defined earlier
    extracted_audio_path = file_id+"-extracted.mp3"
    extract_audio_from_video(video_path, extracted_audio_path)

    # Step 2: Transcribe and censor the extracted audio.
    transcription_result = load_and_transcribe_audio(extracted_audio_path, MODEL_SIZE, DEVICE_TYPE, LANGUAGE)

    # Step 3: Using the extracted audio and transcript make a censored mp3.
    censored_audio_path = file_id + "-censored.mp3"
    beep_swears(extracted_audio_path, file_id, transcription_result, swear_list)

    # Step 4: using the original video and the censored audio, merge to make censored video.
    output_video_path = file_id + "-censored.mp4"
    replace_audio_in_video(video_path, censored_audio_path, output_video_path)



    return output_video_path

if __name__ == "__main__":
    # Input your file and swear list here
    video_file_path = "test-video.mp4"  # Specify the video file you want to process

    process_video(video_file_path)
