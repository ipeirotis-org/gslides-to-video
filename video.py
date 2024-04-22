from moviepy.editor import concatenate_videoclips, AudioFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from itertools import chain
import hashlib
import os

from google_services import initialize_google_services
from google.oauth2 import service_account


# Initialize Google Cloud services
_, storage_client, _, _, _ = initialize_google_services()
bucket_name = "gslide_videos"
bucket = storage_client.bucket(bucket_name)

def generate_md5_hash(filepath):
    """Generate an MD5 hash for a given file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def generate_combined_md5(filepaths):
    """Generate a combined MD5 hash for a list of filepaths."""
    combined_hashes = ''
    for filepath in filepaths:
        combined_hashes += generate_md5_hash(filepath)
    return hashlib.md5(combined_hashes.encode()).hexdigest()

# Check if file exists in Google Cloud Storage
def file_exists_in_gcs(md5_hash):
    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:
        if md5_hash in blob.name:
            return True, f"gs://{bucket_name}/{blob.name}"
    return False, None



def create_video(slides_service, presentation_id, output_dir, output_file):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_count = len(slides)  # This should be the number of slides you have

    clips = []

    files = []

    # Loop through each slide and its corresponding audio
    for i in range(slide_count):
        image_path = f"{output_dir}/slide_{i}.png"
        audio_path = f"{output_dir}/slide_{i}.mp3"

        files.append(image_path)
        files.append(audio_path)

        # Load the audio clip and get its duration
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        print(f"Slide {i}, duration {audio_duration}")

        # Create a video clip from the image and set its duration to match the audio

        img_clip = ImageClip(image_path, duration=audio_duration)

        # Add the audio to this image clip
        img_clip = img_clip.set_audio(audio_clip)

        clips.append(img_clip)

    md5hash = generate_combined_md5(files)

    exists, file_path =  file_exists_in_gcs(md5hash)
    if exists:
        print(f"File already exists: {file_path}")
        # Download the file from GCS to outputfile
        blob = bucket.blob(file_path.replace(f"gs://{bucket_name}/", ""))
        blob.download_to_filename(outputfile)
        print(f"File downloaded to: {outputfile}")

    # Add cross-fade transitions between each pair of clips
    transitions = []
    for i in range(len(clips) - 1):
        crossfade_duration = 1  # The duration of the crossfade

        transition_clip = CompositeVideoClip(
            [clips[i].crossfadeout(crossfade_duration), clips[i + 1].crossfadein(crossfade_duration)], use_bgclip=True
        )
        transition_clip = transition_clip.set_duration(crossfade_duration)
        transition_clip = transition_clip.set_audio(None)

        transitions.append(transition_clip)

    # Export the video
    interleaved = list(chain.from_iterable(zip(clips, transitions))) + [clips[-1]]

    filename = f"gs://{bucket_name}/{output_dir}/{output_file}-{md5hash}.mp4"
    final_clip = concatenate_videoclips(interleaved, method="chain")
    final_clip.write_videofile(f"{output_dir}/{md5hash}.mp4", codec="libx264", threads=32, fps=24)

    return filename
