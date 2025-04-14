from __future__ import division
import pandas as pd
import numpy as np
import os, glob, sys, torch, shutil, random, math, time, cv2
# import torch.backends.cudnn as cudnn
import argparse
from tqdm import tqdm
import cupy as cp

from davide_dp.XVFI import denorm255_np, RGBframes_np2Tensor
from davide_dp.configs import read_config
from davide_dp.utils import (
    is_step_complete,
    log_step_event,
    update_summary_for_video,
    imsaveTensor,
    VideoDataset,
)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates blurry and sharp rgb frames for video id')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')
    parser.add_argument("--gpu", type=int, default=0, help='gpu index')

    args = parser.parse_args(argv)
    return args


def apply_crf(frame_linear, crf_inv, device: torch.device):
    C, H, W = frame_linear.shape
    with cp.cuda.Device(device.index):
        x_r = cp.asarray(crf_inv[:, 0])
        x_g = cp.asarray(crf_inv[:, 1])
        x_b = cp.asarray(crf_inv[:, 2])
        # print('crf_inv to cupy done')

        y = cp.arange(0, 256, 1)

        xp = cp.asarray(frame_linear.reshape(C, -1))
        # print('frames_linear to cupy done')

        yp_r = cp.interp(xp[0], x_r, y)
        yp_g = cp.interp(xp[1], x_g, y)
        yp_b = cp.interp(xp[2], x_b, y)
        # print('interp done')

        yp_r = cp.reshape(yp_r, (H, W))
        yp_g = cp.reshape(yp_g, (H, W))
        yp_b = cp.reshape(yp_b, (H, W))
        yp = cp.stack((yp_r, yp_g, yp_b), axis=0)
    # print('array to tensor done')

    frame = torch.as_tensor(yp, device=device).sub_(0.5).clamp_(0, 255)
    frame = (frame / 255.0 - 0.5) * 2

    return frame


def apply_crf_inv(frames, crf_inv, device: torch.device):
    B, C, H, W = frames.shape
    #verify crf_inv in device
    if crf_inv.device != device:
        crf_inv = crf_inv.to(device)
    # verify frames in device
    if frames.device != device:
        frames = frames.to(device)
    frames_linear = frames.detach().clone()
    # range [0, 1]
    frames_linear = frames_linear.mul_(0.5).add_(0.5)
    # range [0, 255]
    frames_linear = frames_linear.permute(0,2,3,1).reshape(-1, C).mul_(255).add_(0.5).clamp_(0, 255).long()
    # apply crf_inv
    frames_linear = torch.gather(crf_inv, 0, frames_linear).reshape(B, H, W, C).permute(0,3,1,2)
    return frames_linear
    

def save_frames(blurry, sharp, blurry_dir, sharp_dir, filename):
    blurry_path = os.path.join(blurry_dir, filename)
    sharp_path = os.path.join(sharp_dir, filename)
    imsaveTensor(blurry_path, blurry)
    imsaveTensor(sharp_path, sharp)


def main(argv=None):
    args = parse_args(argv)
    config = read_config(args.config)
    idx = args.id

    # Get root directory
    root_dir = config['DAVIDE-tmp']['ROOT']
    # Get video list
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()

    # Check if step 2 is done
    if not is_step_complete(dp_step='step_2', videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
        raise ValueError(f"Step 2 is not done yet for video {video_list[idx]}. Check dp log.")

    # Input and output video paths
    input_video_dir = os.path.join(root_dir, video_list[idx], config['DAVIDE-tmp']['VFI_folder'])
    print('Input video dir: ', input_video_dir)
    blurry_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['blur_folder'])
    sharp_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['sharp_folder'])
    os.makedirs(blurry_dir, exist_ok=True)
    os.makedirs(sharp_dir, exist_ok=True)
    
    # GPU devices
    device = torch.device(
        'cuda:' + str(args.gpu) if torch.cuda.is_available() else 'cpu')  # will be used as "x.to(device)"
    torch.cuda.set_device(device)  # change allocation of current GPU
    # caution!!!! if not "torch.cuda.set_device()":
    # RuntimeError: grid_sampler(): expected input and grid to be on same device, but input is on cuda:1 and grid is on cuda:0
    print('Available devices: ', torch.cuda.device_count())
    print('Current cuda device: ', torch.cuda.current_device())
    print('Current cuda device name: ', torch.cuda.get_device_name(device))
    if args.gpu is not None and torch.cuda.is_available():
        print("Use GPU: {} is used".format(args.gpu))
        # cudnn.benchmark = True
    
    # Read CRF
    crf_inv = torch.load(config['CRF_calibration']['crf_file']).to(device)
    
    # Data loader
    video_dataset = VideoDataset(input_video_dir, config)
    multiple = config['DATA-GEN-PARAMS']['sr_factor']
    dataloader = torch.utils.data.DataLoader(video_dataset, batch_size=multiple, drop_last=True, shuffle=False, num_workers=3)

    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1
    blurry, sharp, filename = None, None, None
    frames_name = [os.path.basename(x) for x in video_dataset.frames_path]
    with torch.no_grad():
        for batchIdx, (frames, framesIds) in tqdm(enumerate(dataloader)):

            frames = frames.to(device)
            # get irradiance values
            frames_linear = apply_crf_inv(frames, crf_inv, device)

            if (batchIdx % num_frames) == 0:
                blurry = 1/num_frames * torch.mean(frames_linear, dim=0, keepdim=False)
            else:
                blurry += 1/num_frames * torch.mean(frames_linear, dim=0, keepdim=False)
            
            if (batchIdx % num_frames) == middle_frame_num:
                sharp = frames[0]
                # CHANGED: replaced .numpy() with .item():
                filename = frames_name[framesIds[0].item()].split("_")[0] + ".png"
            if (batchIdx % num_frames) == num_frames - 1:
                blurry = apply_crf(blurry, crf_inv, device)
                save_frames(blurry, sharp, blurry_dir, sharp_dir, filename)
    
    # Update dp log
    log_step_event(video_name=video_list[idx], dp_step='step_3', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 2 completed for video {video_list[idx]}.")


if __name__ == '__main__':
    sys.exit(main())