# import requests
# import time
#
# # Replace with your Play.ht API credentials
# USER_ID = "UMEnD1BkBsdby9l0LfjljjL9WwO2"
# API_KEY = "ak-1c60b9e0773c4fa2b54e9601dff46c7b"
#
# def generate_tts(text, voice="s3://play.ht/standard/oliver.mp3"):
#     headers = {
#         "accept": "application/json",
#         "content-type": "application/json",
#         "Authorization": API_KEY,
#         "X-User-ID": USER_ID
#     }
#
#     payload = {
#         "voice": voice,
#         "content": [text],
#         "title": "PlayHT-TTS-Demo"
#     }
#
#     # Step 1: Initiate TTS conversion
#     response = requests.post("https://api.play.ht/api/v2/tts/stream", json=payload, headers=headers)
#     response.raise_for_status()
#     transcription_id = response.json()["transcriptionId"]
#
#     # Step 2: Poll for audio URL
#     audio_url = None
#     while True:
#         status_res = requests.get(f"https://api.play.ht/api/v2/tts/stream/{transcription_id}", headers=headers)
#         status = status_res.json()
#         if status.get("audioUrl"):
#             audio_url = status["audioUrl"]
#             break
#         print("⏳ Waiting for audio generation...")
#         time.sleep(2)
#
#     print(f"✅ Audio URL: {audio_url}")
#     return audio_url
#
# # Example usage
# generate_tts("Hey! This is a test using Play.ht API.")
from pyht import Client
from pyht.client import TTSOptions


client = Client(
    user_id="UMEnD1BkBsdby9l0LfjljjL9WwO2",
    api_key="ak-1c60b9e0773c4fa2b54e9601dff46c7b",
)
options = TTSOptions(voice="s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json")
# Open a file to save the audio
with open("output_jenn.wav", "wb") as audio_file:
    for chunk in client.tts("Hi, I'm Jennifer from Play. How can I help you today?", options, voice_engine = 'PlayDialog-http'):
        # Write the audio chunk to the file
        audio_file.write(chunk)

print("Audio saved as output_jenn.wav")