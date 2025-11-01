import base64
import gc
import os
import tempfile
import time
import uuid

import azure.cognitiveservices.speech as speechsdk
from django.core.files.storage import default_storage

from model_integrations.constants import GCP_LANGUAGE_MAP, LANGUAGE_MAP
from model_integrations.helper.helper import (
    check_user_subscription,
    reduce_character_credits,
)



def azure_tts(
    text,
    voice_name,
    user,
    region,
    subscription_key,
    audio_format="MP3",
):
    try:
        if not check_user_subscription(user):
            raise ValueError("User does not have an active subscription.")
        if not reduce_character_credits(user, len(text)):
            raise ValueError("User does not have enough character credits.")

        # Set up Azure TTS client
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, region=region
        )
        print(speech_config.get_voice_name())
        speech_config.speech_synthesis_voice_name = voice_name

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{audio_format.lower()}",
            dir=default_storage.location,
        ) as tmp_file:
            temp_file_path = tmp_file.name
            temp_filename = os.path.basename(temp_file_path)

        # Set up audio config to write to the temp file
        audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file_path)

        # Create the synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Synthesize the speech
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Read and encode the audio
            with open(temp_file_path, "rb") as audio_file:
                audio_content = audio_file.read()
                audio_base64 = base64.b64encode(audio_content).decode("utf-8")

            # Ensure all handles are closed and memory is cleared
            time.sleep(1)
            gc.collect()

            # Delete the temporary file
            try:
                os.remove(temp_file_path)
            except Exception as delete_error:
                print(f"Warning: Failed to delete temp file: {delete_error}")

            return True, {
                "filename": temp_filename,
                "audio_base64": audio_base64,
                "format": audio_format,
            }

        else:
            if result.reason == speechsdk.ResultReason.Canceled:
                error_details = result.cancellation_details.error_details
                return False, error_details
            return False, "Unknown error"

    except Exception as e:
        return False, str(e)


def azure_populate_voices_table(
    azure_subscription_key, azure_region
):
    """
    Fetch the list of supported voices from Azure TTS and populate the Voice model.
    """
    from model_voices_app.models import Voice
    from model_config_app.models import Configuration

    # Get or create the Configuration for Azure
    config = Configuration.objects.get(model_name="azure")
    if not config:
        raise ValueError("Azure configuration not found.")
    if not azure_subscription_key or not azure_region:  # Ensure keys are set
        print("Azure subscription key or region is not set.")
        raise ValueError("Azure subscription key or region is required.")

    speech_config = speechsdk.SpeechConfig(
        subscription=azure_subscription_key, region=azure_region
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.get_voices_async().get()

    for v in result.voices:
        locale = getattr(v, "locale", "")
        language = GCP_LANGUAGE_MAP.get(locale.lower(), None)
        voicename = getattr(v, "name", "")
        voice_id = getattr(v, "short_name", "") or voicename
        gender = getattr(v, "gender", "").name if hasattr(v, "gender") else ""
        sample_url = ""  # Azure does not provide sample URLs directly
        style_list = (
            ",".join(getattr(v, "style_list", []))
            if getattr(v, "style_list", [])
            else ""
        )
        if language:
            Voice.objects.update_or_create(
                voice_id=voice_id,
                defaults={
                    "language": language,
                    "language_code": locale,
                    "voicename": voicename,
                    "gender": gender,
                    "sample_url": sample_url,
                    "style_list": style_list,
                    "is_active": True,
                    "model": config,
                },
            )
    print("Voice model populated from Azure voices.")
