import os
from google.cloud import firestore
from config import BUCKET_NAME
import hashlib
from google_services import access_secret_version, initialize_google_services


# Initialize Google Cloud services
_, storage_client, firestore_client, secrets_client, _ = initialize_google_services()

def upload_to_bucket(storage_client, blob_name, file_path):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"

def add_firestore_entry(firestore_client, collection_name, document_id, metadata):
    doc_ref = firestore_client.collection(collection_name).document(document_id)
    doc_ref.set(metadata)

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Check if file exists in Google Cloud Storage
def file_exists_in_gcs(md5_hash, voice_id):
    blobs = storage_client.list_blobs(BUCKET_NAME)
    for blob in blobs:
        if md5_hash in blob.name and voice_id in blob.name:
            return True, f"gs://{BUCKET_NAME}/{blob.name}"
    return False, None


# Function to generate MD5 hash
def generate_md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()



# Save file to Google Cloud Storage
def save_file_to_gcs(audio, md5_hash, voice_id):
    file_path = f"audio/{voice_id}/{md5_hash}.mp3"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_path)
    blob.upload_from_string(audio, content_type="audio/mpeg")
    return f"gs://{BUCKET_NAME}/{file_path}"
