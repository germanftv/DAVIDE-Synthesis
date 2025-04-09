import sys
import os
from configs import read_config
import argparse

from utils import check_log_step, update_log_step
import XVFI

def main_parser(argv=None):
    parser = argparse.ArgumentParser(description='XVFI Wrapper')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')
    parser.add_argument("--gpu", type=int, default=0, help='gpu index')

    args = parser.parse_args(argv)
    return args, parser


def main(args, parser):
    config = read_config(args.config)
    idx = args.id

    # Get root directory and video list
    root_dir = config['DAVIDE-tmp']['ROOT']
    video_list = os.listdir(root_dir)
    video_list.sort()
    
    # Check if step 1 is done
    if not check_log_step(config['DATA-GEN-PARAMS']['dp_log'], video_list[idx], 1):
        print('Step 1 is not done yet')
        return

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

    # Update info log
    update_log_step(config['DATA-GEN-PARAMS']['dp_log'], video_list[idx], 2)


if __name__ == '__main__':
    args, parser = main_parser(sys.argv[1:])
    main(args, parser)