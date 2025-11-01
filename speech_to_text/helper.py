from openai import OpenAI


def speech_to_text(api_key: str, audio_file: str) -> str:
    client = OpenAI(api_key=api_key)
    try:
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", file=audio_file.read(), response_format="text"
        )
        return transcription.text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def lemonfox_stt(api_key: str, audio_file) -> str:
    """
    Convert speech to text using LemonFox STT API.

    Args:
        api_key (str): LemonFox API key
        audio_file: Audio file object (must be compatible with OpenAI's audio.transcriptions.create)

    Returns:
        str: Transcribed text

    Raises:
        Exception: If the API request fails
    """
    try:
        # Initialize OpenAI client with LemonFox base URL
        client = OpenAI(api_key=api_key, base_url="https://api.lemonfox.ai/v1")

        # Create transcription using OpenAI-compatible endpoint
        response = client.audio.transcriptions.create(
            model="whisper-1",  # LemonFox uses Whisper model
            file=audio_file,
            response_format="text",
        )

        return response

    except Exception as e:
        raise Exception(f"LemonFox speech-to-text failed: {str(e)}")
