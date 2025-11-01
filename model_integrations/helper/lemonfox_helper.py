import io
from openai import OpenAI
from model_integrations.helper.helper import check_user_subscription, reduce_character_credits
from model_voices_app.models import Voice
from model_config_app.models import Configuration


def get_lemonfox_voices(api_key: str) -> list:
    """
    Fetch available voices from LemonFox TTS API.

    Args:
        api_key (str): LemonFox API key

    Returns:
        list: List of available voices with their details

    Raises:
        Exception: If the API request fails
    """
    try:
        # Initialize OpenAI client with LemonFox base URL
        client = OpenAI(api_key=api_key, base_url="https://api.lemonfox.ai/v1")

        # Fetch voices using OpenAI-compatible endpoint
        response = client.models.list()

        # Filter and format the response to get voice-specific information
        voices = []
        for model in response.data:
            if model.id.startswith("tts"):  # Assuming voice models have 'tts' prefix
                voice_info = {
                    "voice_id": model.id,
                    "voicename": model.name if hasattr(model, "name") else model.id,
                    "description": (
                        model.description if hasattr(model, "description") else ""
                    ),
                    # Default values for required fields
                    "language": "en",  # Default to English
                    "language_code": "en-US",  # Default to US English
                    "gender": "",  # Empty as not provided by API
                    "sample_url": "",  # Empty as not provided by API
                    "style_list": "",  # Empty as not provided by API
                }
                voices.append(voice_info)

        return voices

    except Exception as e:
        raise Exception(f"Failed to fetch LemonFox voices: {str(e)}")


def populate_lemonfox_voices_table(api_key: str = None):
    """
    Fetch the list of supported voices from LemonFox and populate the Voice model.

    Args:
        api_key (str, optional): LemonFox API key. If not provided, will try to get from Configuration.

    Returns:
        None
    """
    config = Configuration.objects.filter(
        provider="lemonfox", active=True, is_tts=True
    ).first()
    if not config:
        raise Exception("LemonFox Config not found or inactive")
    if not api_key:
        if not config or not config.api_key:
            raise Exception("LemonFox API key not configured")
        api_key = config.api_key

    # Fetch voices from LemonFox API
    voices = get_lemonfox_voices(api_key)

    # Update or create voice entries in the database
    for voice_data in voices:
        Voice.objects.update_or_create(
            voice_id=voice_data["voice_id"],
            defaults={
                "voicename": voice_data["voicename"],
                "language": voice_data["language"],
                "language_code": voice_data["language_code"],
                "gender": voice_data["gender"],
                "sample_url": voice_data["sample_url"],
                "style_list": voice_data["style_list"],
                "is_active": True,
                "model": config,
            },
        )

    print("Voice model populated from LemonFox voices.")


def lemonfox_tts(
    text: str, voice: str, model: str, response_format: str, api_key: str, user=None
):
    """
    Generate speech using LemonFox TTS API.

    Args:
        text (str): Text to convert to speech
        voice (str): Voice ID/name to use
        model (str): Model to use (e.g., 'tts-1')
        response_format (str): Output format (e.g., 'mp3')
        api_key (str): LemonFox API key
        user (User, optional): User making the request

    Returns:
        tuple: (audio_content_base64, format)

    Raises:
        Exception: If the API request fails
    """
    try:
        if not check_user_subscription(user):
            raise ValueError("User does not have an active subscription.")
        if not reduce_character_credits(user, len(text)):
            raise ValueError("User does not have enough character credits.")
        # Initialize OpenAI client with LemonFox base URL
        client = OpenAI(api_key=api_key, base_url="https://api.lemonfox.ai/v1")

        # Create speech using OpenAI-compatible endpoint
        audio_response = client.audio.speech.create(
            model=model, voice=voice, response_format=response_format, input=text
        )

        # Create an in-memory bytes buffer
        buffer = io.BytesIO()
        for chunk in audio_response.iter_bytes():
            buffer.write(chunk)

        # Convert to base64
        import base64

        audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return audio_base64, response_format

    except Exception as e:
        raise Exception(f"LemonFox TTS generation failed: {str(e)}")
