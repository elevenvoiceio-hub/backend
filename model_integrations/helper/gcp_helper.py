import base64
from model_integrations.constants import GCP_LANGUAGE_MAP
from model_integrations.helper.azure_helper import azure_populate_voices_table
from model_integrations.helper.eleven_labs_helper_api import (
    populate_elevenlabs_voices_table,
)
from model_integrations.helper.helper import (
    check_user_subscription,
    reduce_character_credits,
)
from model_integrations.helper.modellabs_helper import populate_modellabs_voices_table
from model_integrations.helper.speechify_helper import populate_voices_table
from model_voices_app.models import Voice
from model_config_app.models import Configuration
from google.cloud import texttospeech



def gcp_tts(
    user,
    text,
    language_code,
    voice_name,
    credentials_path,
    audio_format="MP3",  # Default to MP3
    speaking_rate=1.0,
    pitch=0.0,
):
    if not check_user_subscription(user):
        raise ValueError("User does not have an active subscription.")
    if not reduce_character_credits(user, len(text)):
        raise ValueError("User does not have enough character credits.")
    # Use service account from path or default env
    client = texttospeech.TextToSpeechClient.from_service_account_file(credentials_path)

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    populate_elevenlabs_voices_table(
        "sk_b55e604170b64e3e8d31bf7500014bc9b19ceec5d16a37d3"
    )
    # Map format string to GCP enum
    format_map = {
        "MP3": texttospeech.AudioEncoding.MP3,
        "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        "LINEAR16": texttospeech.AudioEncoding.LINEAR16,  # WAV
    }

    audio_encoding = format_map.get(audio_format.upper())
    if not audio_encoding:
        raise ValueError(f"Unsupported audio format: {audio_format}")

    audio_config = texttospeech.AudioConfig(
        audio_encoding=audio_encoding,
        speaking_rate=speaking_rate,
        pitch=pitch,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Generate a filename
    extension = audio_format.lower() if audio_format.lower() != "linear16" else "wav"
    filename = f"gcp_tts_output.{extension}"

    # Encode audio content to base64
    base64_audio = base64.b64encode(response.audio_content).decode("utf-8")

    return {"filename": filename, "audio_base64": base64_audio, "format": audio_format}


def populate_voice_model_from_gcp(model_name="GCP"):

    # Use service account from path or default env
    client = texttospeech.TextToSpeechClient.from_service_account_file(credentials_path)
    voices = client.list_voices().voices

    # Get or create the Configuration for GCP
    config, _ = Configuration.objects.get_or_create(provider=model_name)

    for voice in voices:
        language_code = voice.language_codes[0] if voice.language_codes else ""
        language_short = language_code.split("-")[0] if language_code else ""
        # Use fallback mapping or default to code
        language = GCP_LANGUAGE_MAP.get(
            language_code.lower(), language_short.capitalize()
        )

        voicename = voice.name
        voice_id = voice.name

        gender = (
            voice.ssml_gender.name
            if hasattr(voice.ssml_gender, "name")
            else str(voice.ssml_gender)
        )
        sample_url = ""  # GCP does not provide sample URLs directly
        style_list = ""  # Not available in GCP response

        Voice.objects.update_or_create(
            voice_id=voice_id,
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
    print("Voice model populated from GCP voices.")
