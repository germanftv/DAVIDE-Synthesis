from __future__ import division
import pandas as pd
import numpy as np
import os, glob, sys, torch, shutil, random, math, time, cv2
import torch.backends.cudnn as cudnn
import argparse
from tqdm import tqdm
import cupy as cp

from davide_dp.XVFI import denorm255_np, RGBframes_np2Tensor
from davide_dp.configs import read_config
from davide_dp.utils.progress_db import is_step_complete, log_step_event, update_summary_for_video
from davide_dp.utils import  read_depth_bin, read_conf_bin, save_depth_16bits, save_conf_8bits


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates blurry and sharp rgb frames for video id')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')

    args = parser.parse_args(argv)
    return args



def main(argv=None):
    # Parse arguments and read config
    args = parse_args(argv)
    config = read_config(args.config)
    idx = args.id

    # Get root directory and video list
    root_dir = config['DAVIDE-raw']['ROOT']
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()
    input_video_dir = os.path.join(root_dir, video_list[idx])
    print('Input video dir: ', input_video_dir)

    # Check if step 1 is done
    if not is_step_complete(dp_step='step_1', videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
        raise ValueError(f"Step 1 is not done yet for video {video_list[idx]}. Check dp log.")

    # Input and output paths
    input_depth_dir = os.path.join(input_video_dir, config['DAVIDE-raw']['depth_folder'])
    input_conf_dir = os.path.join(input_video_dir, config['DAVIDE-raw']['confidence_folder'])
    output_depth_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['depth_folder'])
    output_conf_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['confidence_folder'])
    rgb_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['rgb_folder'])
    os.makedirs(output_depth_dir, exist_ok=True)
    os.makedirs(output_conf_dir, exist_ok=True)

    # Read first frame in rgb_dir to get image size
    first_frame = cv2.imread(os.path.join(rgb_dir, os.listdir(rgb_dir)[0]))
    H, W, _ = first_frame.shape

    # Get frames names
    frames_name = os.listdir(rgb_dir)
    frames_name.sort()

    # Get depth and confidence files
    depth_frames = os.listdir(input_depth_dir)
    depth_frames.sort()
    conf_frames = os.listdir(input_conf_dir)
    conf_frames.sort()

    # Drop last frame (due to interpolation)
    depth_frames = depth_frames[:-1]
    conf_frames = conf_frames[:-1]
    frames_name = frames_name[:-1]

    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1

    # Drop frames that are not multiple of num_frames
    N = len(depth_frames) // num_frames * num_frames
    depth_frames = depth_frames[:N]
    conf_frames = conf_frames[:N]
    frames_name = frames_name[:N]
    
    for batchIdx, (depth_frame, conf_frame, file_name) in tqdm(enumerate(zip(depth_frames, conf_frames, frames_name))):
        if (batchIdx % num_frames) == middle_frame_num:
            # Read depth and confidence frames
            depth = read_depth_bin(os.path.join(input_depth_dir, depth_frame), img_shape=(H, W))
            conf = read_conf_bin(os.path.join(input_conf_dir, conf_frame), img_shape=(H, W))
            # Save depth and confidence frames
            save_depth_16bits(depth, os.path.join(output_depth_dir, file_name))
            save_conf_8bits(conf, os.path.join(output_conf_dir, file_name))

    # Update dp log
    log_step_event(video_name=video_list[idx], dp_step='step_4', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 4 completed for video {video_list[idx]}.")


if __name__ == '__main__':
    sys.exit(main())