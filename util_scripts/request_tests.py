
import json
import requests


# Utility script.


# Define the API endpoint
url = 'http://localhost:5001/beep_swears'  # Ensure this is your actual API URL

# Path to the audio file you want to test with
audio_file_path = '/test.mp3'


# List of swear words
swear_words = ["word1", "word2", "word3"]  # Replace with actual swear words


# Open the audio file in binary mode
with open(audio_file_path, 'rb') as audio_file:
    files = {'audio': audio_file}
    # Pass the swear list as part of the JSON data
    response = requests.post(url, files=files, data={'swear_list': json.dumps(swear_words)})


# Print the status code of the response
print('Status Code:', response.status_code)

# Attempt to get the JSON response
try:
    print('Response JSON:', response.json())
except ValueError:
    print('Response content:', response.content)
