import params as params
import shutil
import os
from datetime import datetime
from helper_script import youtube_helper
import pandas as pd
from custom_logger import CustomLogger
from logmod import logs


logs(show_level='info', show_color=True)
logger = CustomLogger(__name__)  # use custom logger
helper = youtube_helper()
counter = 0

# Download the highest quality available videos quality value and update it in
# the csv file
df = pd.read_csv(params.input_csv_file)

youtube_links = df["videos"]

for link in youtube_links:
    # Download the youtube video to the local system
    video_ids = [id.strip() for id in link.strip("[]").split(',')]
    for vid in video_ids:
        result = helper.download_video_with_resolution(video_id=vid, output_path=params.output_path)

        if result:
            video_file_path, video_title, resolution = result
            print(video_file_path, video_title, resolution)
            print(f"Video title: {video_title}")
            print(f"Video saved at: {video_file_path}")
        else:
            logger.error("Download failed.")

        input_video_path = f"{params.output_path}/{video_title}.mp4"
        output_video_path = f"{params.output_path}/{video_title}_mod.mp4"

        # Trimming of video (if required)
        start_time = params.trim_start
        end_time = params.trim_end

        if start_time is None and end_time is None:
            print("No trimming required")
        else:
            print("Trimming in progress.......")
            helper.trim_video(input_video_path, output_video_path,
                              start_time, end_time)
            os.remove(f"{params.output_path}/{video_title}.mp4")
            print("Deleted the untrimmed video")
            os.rename(output_video_path, input_video_path)

        print(f"{video_title}_{resolution}")

        if params.prediction_mode:
            helper.prediction_mode()

        if params.tracking_mode:
            helper.tracking_mode(input_video_path, output_video_path)
            if params.need_annotated_video:
                helper.create_video_from_images(
                    params.frames_output_path,
                    params.final_video_output_path, 30)

            data_folder = "data"
            os.makedirs(data_folder, exist_ok=True)
            helper.merge_txt_files(params.txt_output_path,
                                   f"data/{video_title}.csv")

            shutil.rmtree("runs/detect/predict")
            if params.delete_frames:
                shutil.rmtree("runs/detect/frames")

            helper.rename_folder(
                "runs/detect", f"runs/{video_title}_{resolution}_{datetime.now()}"
            )
            counter += 1

        if params.delete_youtube_video:
            os.remove(f"video/{video_title}.mp4")
