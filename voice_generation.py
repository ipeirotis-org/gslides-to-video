import elevenlabs 
from elevenlabs import Voice, VoiceSettings
from google.cloud import firestore, storage
import hashlib
from google_services import access_secret_version, initialize_google_services
from google.oauth2 import service_account
from utils import generate_md5_hash, file_exists_in_gcs, save_file_to_gcs

# Initialize Google Cloud services
_, storage_client, firestore_client, secrets_client, _ = initialize_google_services()

# Initialize ElevenLabs
ELEVEN_LABS_KEY = access_secret_version(secrets_client, "elevenlabs_api_key")
elevenlabs.set_api_key(ELEVEN_LABS_KEY)


bucket_name = "gslide_videos"
bucket = storage_client.bucket(bucket_name)


def get_voices():
    panos = Voice(
        voice_id="z3zYFzY2KtTTLjvOecBO",
        name="Panos Ipeirotis",
        settings=VoiceSettings(stability=0.5, similarity_boost=1.0, style=0.4, use_speaker_boost=True),
    )

    foster = Voice(
        voice_id="4DwOdUD1I2L22bWXNkjs",
        name="Foster",
        settings=VoiceSettings(stability=0.5, similarity_boost=1.0, style=0.4, use_speaker_boost=True),
    )

    michael = Voice(
        voice_id="flq6f7yk4E4fJM5XTYuZ",
    )

    return {"panos": panos, "foster": foster, "michael": michael}




# Save metadata to Firestore
def save_metadata_to_firestore(md5_hash, voice_id, file_path, clip_length):
    doc_ref = firestore_client.collection("audio_files").document(md5_hash)
    doc_ref.set(
        {
            "md5_hash": md5_hash,
            "voice_id": voice_id,
            "file_path": file_path,
            "upload_time": firestore.SERVER_TIMESTAMP,
            "clip_length": clip_length,  # You need to calculate this based on the audio file
            "additional_metadata": {},
        }
    )


def get_audio_from_text(voice, text, outputfile):
    voices = get_voices()
    chosen_voice = voices[voice]

    md5_hash = generate_md5_hash(text)
    exists, file_path = file_exists_in_gcs(md5_hash, chosen_voice.voice_id)

    if exists:
        print(f"File already exists: {file_path}")
        # Download the file from GCS to outputfile
        blob = bucket.blob(file_path.replace(f"gs://{bucket_name}/", ""))
        blob.download_to_filename(outputfile)
        print(f"File downloaded to: {outputfile}")
        return

    # API call to ElevenLabs to get the voice
    audio = elevenlabs.generate(
        text=text,
        voice=chosen_voice,
        model="eleven_monolingual_v1",
    )

    # Save the audio to Google Cloud Storage
    gcs_path = save_file_to_gcs(audio, md5_hash)

    # Save metadata to Firestore
    save_metadata_to_firestore(md5_hash, chosen_voice.voice_id, gcs_path, clip_length=0)  # Update clip_length appropriately

    # Save the audio to a file locally (optional)
    with open(outputfile, "wb") as f:
        f.write(audio)
