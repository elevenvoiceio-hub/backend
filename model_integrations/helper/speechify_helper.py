from speechify import Speechify
from model_integrations.constants import GCP_LANGUAGE_MAP, LANGUAGE_MAP
from model_integrations.helper.helper import (
    check_user_subscription,
    reduce_character_credits,
)
from model_voices_app.models import Voice
from model_config_app.models import Configuration
import requests
import base64


def populate_voices_table(api_key: str):
    client = Speechify(
        token=api_key,
    )
    resp = client.tts.voices.list()

    # Get or create the Configuration for Speechify
    config = Configuration.objects.filter(provider="speechify", active=True).first()
    for voice in resp:
        voicename = getattr(voice, "display_name", "")
        voice_id = getattr(voice, "id", "")
        gender = getattr(voice, "gender", "")
        sample_url = getattr(voice, "preview_audio", "")
        style_list = ""
        language_code = getattr(voice, "locale", "")
        voice_type = getattr(voice, "type", "")  # Get the voice type
        language = GCP_LANGUAGE_MAP.get(language_code.lower(), None)

        # Only add voices that are of type 'shared' or if language is available
        if language and voice_type == "shared":
            Voice.objects.update_or_create(
                voice_id=f"{voice_id}",
                defaults={
                    "language": language,
                    "language_code": language_code,
                    "voicename": voicename,
                    "gender": gender,
                    "sample_url": sample_url,
                    "style_list": style_list,
                    "is_active": True,
                    "model": config,
                },
            )

    print("Voice model populated from Speechify voices.")


def speechify_tts(
    user,
    text: str,
    voice_id: str,
    output_format: str = "mp3",  # "mp3", "ogg", "wav"
    token: str = None,
) -> str:
    """
    Generate speech audio from Speechify TTS API and return base64-encoded audio.
    Note: Speechify API does not support pitch and speaking_rate parameters.
    """
    if not check_user_subscription(user):
        raise ValueError("User does not have an active subscription.")
    if not reduce_character_credits(user, len(text)):
        raise ValueError("User does not have enough character credits.")
    if not text or not voice_id:
        raise ValueError("Both 'text' and 'voice_id' are required.")

    client = Speechify(token=token)
    try:
        response = client.tts.audio.speech(input=text, voice_id=voice_id)
    except Exception as e:
        raise RuntimeError(f"Speechify TTS request failed: {e}")

    return response.audio_data, response.audio_format
