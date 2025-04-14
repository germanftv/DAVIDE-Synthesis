from __future__ import division
import pandas as pd
import numpy as np
import os, sys
import torch
import argparse
from tqdm import tqdm
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from davide_dp.configs import read_config
from davide_dp.utils import (
    is_step_complete,
    log_step_event,
    update_summary_for_video
)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates blurry and sharp rgb frames for video id')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--rgb_dir", type=str, required=True, choices=['blur', 'sharp'], help='Input rgb frames directory. Options: blur, sharp')
    parser.add_argument("--id", type=int, required=True, help='Video id')

    args = parser.parse_args(argv)
    return args


def main(argv=None):
    # Parse arguments and read config
    args = parse_args(argv)
    config = read_config(args.config)
    idx = args.id
    rgb_dir = args.rgb_dir
    checkpoint = config['MONO-DEPTH']['checkpoint']

    # Get root directory and video list
    root_dir = config['DAVIDE-tmp']['ROOT']
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()
    input_video_dir = os.path.join(root_dir, video_list[idx])
    print('Input video dir: ', input_video_dir)

    # Check if step 3 is done
    if not is_step_complete(dp_step='step_3', videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
        raise ValueError(f"Step 3 is not done yet for video {video_list[idx]}. Check dp log.")

    # Input and output paths
    input_dir = os.path.join(input_video_dir, config['DAVIDE-tmp']['{}_folder'.format(rgb_dir)])
    output_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], '{}_{}'.format(config['DAVIDE-tmp']['mono_depth_folder'], rgb_dir))
    os.makedirs(output_dir, exist_ok=True)


    # Get frames names
    frames_name = os.listdir(input_dir)
    frames_name.sort()
    

    ############# Check missing frames ##############
    # ready_frames = os.listdir(output_dir)
    # # Convert lists to sets
    # frames_name_set = set(frames_name)
    # ready_frames_set = set(ready_frames)

    # # Get the frames that are not ready
    # not_ready_frames = frames_name_set - ready_frames_set
    # not_ready_frames = list(not_ready_frames)

    # if not not_ready_frames:
    #     return exit(0)
    #################################################

    # Get image processor and model
    image_processor = AutoImageProcessor.from_pretrained(checkpoint)
    model = AutoModelForDepthEstimation.from_pretrained(checkpoint)
    
    # for file_name in tqdm(not_ready_frames):
    for file_name in tqdm(frames_name):
        # Read input frame
        input_path = os.path.join(input_dir, file_name)
        image = Image.open(input_path)

        # Preprocess image
        pixel_values = image_processor(image, return_tensors="pt").pixel_values

        # Predict depth
        with torch.no_grad():
            outputs = model(pixel_values)
            predicted_depth = outputs.predicted_depth

        # Interpolate to original size
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
        output = prediction.numpy()

        formatted = (output * 255 / np.max(output)).astype("uint8")
        depth = Image.fromarray(formatted)

        # Save depth frame
        output_path = os.path.join(output_dir, file_name)
        depth.save(output_path)

    # Update dp log
    log_step_event(video_name=video_list[idx], dp_step='step_7', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 7 completed for video {video_list[idx]}.")



if __name__ == '__main__':
    sys.exit(main())