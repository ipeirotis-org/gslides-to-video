from video import create_video
from gslides import get_presentation, extract_slides_and_text

# Get presentation and slides
# presentation_id = "1s_41ty_BGC4OzUnzmLhuX_S2eY6I-9QG2cB_eZM02kM" # 7.1
# presentation_id = "1GrQC_1SNItv3usF1WZCiRnzTcDbPHRZoHW7dPm4XbXA" # test
presentation_id = "1BgL7sTbfrOa2vSwgDF14pWyx6URWdMqrE1JJrhV9Wjw" # 7.2

presentation = get_presentation(presentation_id)

title = presentation.get("title")
output_folder = f'/content/slides/output/{title}'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# If you do not want to cache the audio, delete the audio files
# !rm /content/slides/output/{title}/*

extract_slides_and_text(presentation_id, output_folder)

create_video(presentation_id, output_folder)
