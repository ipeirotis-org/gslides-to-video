from elevenlabs import set_api_key, generate, Voice, VoiceSettings
from google.cloud import firestore, storage
import hashlib
from get_secrets import access_secret_version
from google.oauth2 import service_account

# Initialize Google Cloud services
SERVICE_ACCOUNT_FILE = "gslides-to-video.json"
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
storage_client = storage.Client(credentials=credentials)
db = firestore.Client(credentials=credentials)


ELEVEN_LABS_KEY = access_secret_version("elevenlabs_api_key")
set_api_key(ELEVEN_LABS_KEY)


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

    return {"panos": panos, "foster": foster, "michael": "Michael"}


# Function to generate MD5 hash
def generate_md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


# Check if file exists in Google Cloud Storage
def file_exists_in_gcs(md5_hash):
    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:
        if md5_hash in blob.name:
            return True, "gs://{}/{}".format(bucket_name, blob.name)
    return False, None


# Save file to Google Cloud Storage
def save_file_to_gcs(audio, md5_hash, voice_id):
    file_path = f"audio/{voice_id}/{md5_hash}.mp3"
    blob = bucket.blob(file_path)
    blob.upload_from_string(audio, content_type="audio/mpeg")
    return f"gs://{bucket_name}/{file_path}"


# Save metadata to Firestore
def save_metadata_to_firestore(md5_hash, voice_id, file_path, clip_length):
    doc_ref = db.collection("audio_files").document(md5_hash)
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
    exists, file_path = file_exists_in_gcs(md5_hash)

    if exists:
        print(f"File already exists: {file_path}")
        # Optionally, download the file from GCS to outputfile here
        return

    # API call to ElevenLabs to get the voice
    audio = generate(
        text=text,
        voice=chosen_voice,
        model="eleven_monolingual_v1",
    )

    # Save the audio to Google Cloud Storage
    gcs_path = save_file_to_gcs(audio, md5_hash, chosen_voice.voice_id)

    # Save metadata to Firestore
    save_metadata_to_firestore(md5_hash, chosen_voice.voice_id, gcs_path, clip_length=0)  # Update clip_length appropriately

    # Save the audio to a file locally (optional)
    with open(outputfile, "wb") as f:
        f.write(audio)
