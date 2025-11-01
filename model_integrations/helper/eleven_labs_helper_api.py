import re

import requests
import base64
from typing import Tuple
from model_integrations.constants import GCP_LANGUAGE_MAP, LANGUAGE_MAP
from model_integrations.helper.helper import (
    check_user_subscription,
    reduce_character_credits,
)
from model_voices_app.models import Voice
from model_config_app.models import Configuration
import requests


def populate_elevenlabs_voices_table(api_key: str):
    """
    Fetch the list of supported voices from ElevenLabs and populate the Voice model.
    """
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    voices = data.get("voices", [])

    # Get or create the Configuration for ElevenLabs
    config, _ = Configuration.objects.get_or_create(provider="elevenlabs")

    for voice in voices:
        voicename = voice.get("name", "")
        voice_id = voice.get("voice_id", "")
        # Use voice_id as voice_code for uniqueness
        voicecode = ("E_" + voicename).lower()
        gender = voice.get("labels", {}).get("gender", "")
        sample_url = voice.get("preview_url", "")
        country = voice.get("labels", {}).get("accent", "")
        language_code = voice.get("labels", {}).get("language", "")
        language = GCP_LANGUAGE_MAP.get(language_code.lower(), None)
        # If styles are present in labels, join them
        styles = voice.get("labels", {}).get("style", [])
        style_list = ",".join(styles) if isinstance(styles, list) else str(styles)

        if language:
            Voice.objects.update_or_create(
                voice_id=voice_id,
                voice_code=voicecode,
                country=country,
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

    print("Voice model populated from ElevenLabs voices.")


def get_audio_extension(output_format: str) -> str:
    """
    Determines file extension from the ElevenLabs output_format string.
    """
    # Common formats: mp3_44100_128, wav, pcm_22050, ulaw_8000
    fmt = output_format.lower()
    # If format is just 'mp3', 'wav', etc.
    match = re.match(r"^([a-zA-Z0-9]+)", fmt)
    if match:
        base_fmt = match.group(1)
        # Standardize mp3 aliases
        if base_fmt.startswith("mp3"):
            return "mp3"
        elif base_fmt.startswith("wav"):
            return "wav"
        elif base_fmt.startswith("pcm"):
            return "pcm"
        elif base_fmt.startswith("ulaw"):
            return "ulaw"
        else:
            return base_fmt  # fallback
    return "mp3"  # default


def elevenlabs_tts(
    user,
    text: str,
    voice_id: str,
    api_key: str ,
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
) -> Tuple[str, str]:
    """
    Converts text to speech using the ElevenLabs API and saves the audio to a file.

    Args:
        api_key (str): ElevenLabs API key.
        text (str): Text to convert to speech.
        voice_id (str): Voice ID to use for speech synthesis.
        output_filename (str, optional): Output file name. Defaults to "output.mp3".

    Returns:
        Tuple[str, str]: A tuple containing the output filename and the base64-encoded content of the file.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
    }

    try:
        if not check_user_subscription(user):
            raise ValueError("User does not have an active subscription.")
        if not reduce_character_credits(user, len(text)):
            raise ValueError("User does not have enough character credits.")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Error while calling ElevenLabs API: {e}")

    encoded_content = base64.b64encode(response.content).decode("utf-8")

    filename = f"elevenlabs_tts_output.{output_format}"
    return filename, encoded_content
