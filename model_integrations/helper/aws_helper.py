import boto3

def aws_tts(text, voice_id, output_filename, aws_access_key, aws_secret_key, region_name='us-east-1'):
    # Create a Polly client
    polly_client = boto3.client(
        'polly',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )

    # Request speech synthesis
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=voice_id  # e.g., 'Joanna', 'Matthew', 'Aditi'
    )

    # Save the audio stream
    with open(output_filename, 'wb') as file:
        file.write(response['AudioStream'].read())
        print(f"Speech synthesized and saved to '{output_filename}' using voice: {voice_id}")

# Example usage
aws_tts(
    text="Hello, this is a test using Amazon Polly with a specific voice.",
    voice_id="Joanna",
    output_filename="polly_output.mp3",
    aws_access_key="YOUR_AWS_ACCESS_KEY",
    aws_secret_key="YOUR_AWS_SECRET_KEY",
    region_name="us-east-1"
)
