import base64
import gc
import os
import re
import tempfile
import time
from datetime import datetime

from django.core.files.storage import default_storage
from elevenlabs import ElevenLabs


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


def tts_to_base64(
        text: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
        api_key: str ="sk_b55e604170b64e3e8d31bf7500014bc9b19ceec5d16a37d3",
) :
    """
    Converts text to speech using ElevenLabs and returns (filename, base64_content).
    File extension is determined by output_format.
    Returns (filename, base64_audio_content) or (None, None) on error.
    """
    try:
        final_api_key = api_key
        if not final_api_key:
            raise ValueError("ElevenLabs API key not provided or found in ENV.")
        if not text.strip():
            raise ValueError("Input text is empty.")
        if not voice_id:
            raise ValueError("Voice ID not specified.")

        # Extension from output_format
        ext = get_audio_extension(output_format)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext.lower()}",
                                         dir=default_storage.location) as tmp_file:
            temp_file_path = tmp_file.name
            temp_filename = os.path.basename(temp_file_path)

        client = ElevenLabs(api_key=final_api_key)
        audio_bytes = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
        )
        with open(temp_file_path, "rb") as audio_file:
            audio_content = audio_file.read()
            audio_base64 = base64.b64encode(audio_content).decode("utf-8")

            # Ensure all handles are closed and memory is cleared
        gc.collect()

        # Delete the temporary file
        try:
            os.remove(temp_file_path)
        except Exception as delete_error:
            print(f"Warning: Failed to delete temp file: {delete_error}")


        return {"filename": temp_filename, "audio_base64": audio_base64, "format": audio_format}

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None, None


# Example usage
if __name__ == "__main__":
    VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # Replace with your voice ID
    file_name, b64_audio = tts_to_base64(
        text="Testing ElevenLabs with user-defined file formats.",
        voice_id=VOICE_ID,
        output_format="wav"  # Try with "mp3_44100_128", "wav", etc.
    )
    if file_name and b64_audio:
        print("Filename:", file_name)
        print("Base64 (first 100 chars):", b64_audio[:100])
    else:
        print("TTS conversion failed.")
