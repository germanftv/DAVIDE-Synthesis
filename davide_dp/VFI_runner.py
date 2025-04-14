import sys
import os
import pandas as pd
import argparse

# from utils import check_log_step, update_log_step
from davide_dp.configs import read_config
from davide_dp.utils.progress_db import is_step_complete, log_step_event, update_summary_for_video
import davide_dp.XVFI as XVFI

def main_parser(argv=None):
    parser = argparse.ArgumentParser(description='XVFI Wrapper')
    parser.add_argument("--config", type=str, default='davide_dp/configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')
    parser.add_argument("--gpu", type=int, default=0, help='gpu index')

    args = parser.parse_args(argv)
    return args, parser


def main(args, parser):
    config = read_config(args.config)
    idx = args.id

    # Get root directory
    root_dir = config['DAVIDE-tmp']['ROOT']
    # Get video list
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()
    
    # Check if step 1 is done
    if not is_step_complete(dp_step='step_1', videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
        raise ValueError(f"Step 1 is not done yet for video {video_list[idx]}. Check dp log.")

    # Input and output paths
    input_dir = os.path.join(root_dir, video_list[idx], config['DAVIDE-tmp']['rgb_folder'])
    output_dir = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['VFI_folder'])
    os.makedirs(output_dir, exist_ok=True)

    # XVFI settings
    xvfi_config = config['DATA-GEN-PARAMS']['XVFI_config']

    args.input_dir = input_dir
    args.output_dir = output_dir
    args.pretrained = config['DATA-GEN-PARAMS']['XVFI_pretrained']
    args.config = xvfi_config
    args.multiple = config['DATA-GEN-PARAMS']['sr_factor']
    args = XVFI.add_default_args(args, parser)

    # Run XVFI
    XVFI.run(args)

    # Update dp log
    log_step_event(video_name=video_list[idx], dp_step='step_2', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 2 completed for video {video_list[idx]}.")


if __name__ == '__main__':
    args, parser = main_parser(sys.argv[1:])
    main(args, parser)