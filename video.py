from moviepy.editor import concatenate_videoclips, AudioFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from itertools import chain


def create_video(slides_service, presentation_id, output_dir, output_file):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_count = len(slides)  # This should be the number of slides you have

    clips = []

    # Loop through each slide and its corresponding audio
    for i in range(slide_count):
        image_path = f"{output_dir}/slide_{i}.png"
        audio_path = f"{output_dir}/slide_{i}.mp3"

        # Load the audio clip and get its duration
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        print(f"Slide {i}, duration {audio_duration}")

        # Create a video clip from the image and set its duration to match the audio

        img_clip = ImageClip(image_path, duration=audio_duration)

        # Add the audio to this image clip
        img_clip = img_clip.set_audio(audio_clip)

        clips.append(img_clip)

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

    final_clip = concatenate_videoclips(interleaved, method="chain")
    final_clip.write_videofile(f"{output_dir}/final_video.mp4", codec="libx264", threads=32, fps=24)
