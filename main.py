import sys
import os
from tqdm import tqdm
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build


from video import create_video
from voice_generation import get_voices
from gslides import extract_slide_images, extract_speaker_notes_to_mp3

from google_services import initialize_google_services

def upload_to_bucket(storage_client, blob_name, file_path, bucket_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    return blob.public_url


def add_firestore_entry(firestore_client, presentation_id, metadata):
    doc_ref = firestore_client.collection("presentations").document(presentation_id)
    doc_ref.set(metadata)


def main(presentation_id):
    '''
    The function gets as input the "presentation id" from Google slides.

    The presentation ID is part of the URL. For example, for the presentation at
    https://docs.google.com/presentation/d/1BgL7sTbfrOa2vSwgDF14pWyx6URWdMqrE1JJrhV9Wjw/edit#slide=id.p1

    the presentation ID is "1BgL7sTbfrOa2vSwgDF14pWyx6URWdMqrE1JJrhV9Wjw"

    For the program to access the presentation, the presentation needs to be shared
    with github@gslides-to-video.iam.gserviceaccount.com 
    '''
    
    # We setup all the google services necessary
    slides_service, storage_client, firestore_client, _, _ = initialize_google_services()

    # This gives us programmatic access to the slides
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    title = presentation.get("title")

    # Here we define which ElevenLabs voice we want to use
    # TODO: Make this a parameter from the command line
    voice = "panos"
    voice_id = get_voices().get(voice).voice_id

    # We will save all the output in the local folder under content
    # and we will also mirror everything to a Google Bucket
    output_folder = f"./content/slides/output/{title}/{presentation_id}/{voice_id}"
    output_file = "output_video.mp4"
    video_path = os.path.join(output_folder, output_file)  
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Extract images from slides and saves them as images under the output folder
    extract_slide_images(slides_service, presentation_id, output_folder)

    # Optionally specify a voice for MP3 extraction
    extract_speaker_notes_to_mp3(slides_service, presentation_id, output_folder, voice)
    
    create_video(slides_service, presentation_id, output_folder, output_file)
    
    bucket_name = "gslide_videos"
    video_url = upload_to_bucket(storage_client, f"videos/{title}--{presentation_id}/{voice_id}--{voice}/{output_file}", video_path, bucket_name)
    metadata = {
        "title": title,
        "presentation_id": presentation_id,
        "upload_time": firestore.SERVER_TIMESTAMP,
        "video_url": video_url,
        "voice_id": voice_id,
        "voice": voice,
        "additional_metadata": {},
    }
    add_firestore_entry(firestore_client, f"{presentation_id}--{voice_id}", metadata)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <presentation_id>")
        sys.exit(1)
    presentation_id = sys.argv[1]
    main(presentation_id)
