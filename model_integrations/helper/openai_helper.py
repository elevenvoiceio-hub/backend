import openai

def openai_tts(text, voice, output_filename, api_key):
    openai.api_key = api_key

    response = openai.audio.speech.create(
        model="tts-1",         # or "tts-1-hd" for higher quality
        voice=voice,           # Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
        input=text
    )

    # Save the audio stream
    with open(output_filename, "wb") as f:
        f.write(response.read())
        print(f"Audio saved to '{output_filename}' using voice: {voice}")

# Example usage
openai_tts(
    text="Hello! This is a demo of OpenAI's Text to Speech capabilities.",
    voice="shimmer",
    output_filename="openai_output.mp3",
    api_key="YOUR_OPENAI_API_KEY"
)
