from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

def ibm_tts(text, voice, output_filename, api_key, url):
    # Set up authenticator
    authenticator = IAMAuthenticator(api_key)

    # Initialize TTS client
    text_to_speech = TextToSpeechV1(authenticator=authenticator)
    text_to_speech.set_service_url(url)

    # Synthesize text
    response = text_to_speech.synthesize(
        text=text,
        voice=voice,  # e.g., 'en-US_AllisonV3Voice'
        accept='audio/mp3'
    ).get_result()

    # Save audio to file
    with open(output_filename, 'wb') as audio_file:
        audio_file.write(response.content)
        print(f"Audio saved to '{output_filename}' using voice: {voice}")

# Example usage
ibm_tts(
    text="Hello, this is a test using IBM Watson Text to Speech.",
    voice="en-US_AllisonV3Voice",
    output_filename="ibm_output.mp3",
    api_key="YOUR_IBM_WATSON_API_KEY",
    url="YOUR_IBM_WATSON_URL"  # e.g., "https://api.us-south.text-to-speech.watson.cloud.ibm.com"
)
