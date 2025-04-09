import pandas as pd
import numpy as np
import os
import sys
import argparse
from tqdm import tqdm

from configs import read_config


STEPS = 8


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Create Dataset Processing log file')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    args = parser.parse_args(argv)
    return args


def main(argv=None):
    args = parse_args(argv)
    config = read_config(args.config)

    data_dir = config['DAVIDE-raw']['ROOT']
    dp_log_info_file = config['DATA-GEN-PARAMS']['dp_log']
    
    # Create dataset processing log file
    steps = ['step_{}'.format(i+1) for i in range(STEPS)]
    print('Creating Dataset Processing log file')
    dataset_seqs = os.listdir(data_dir)
    dataset_seqs.sort()
    dataset_info = pd.DataFrame(columns=['recording', *steps, 'total'])
    dataset_info['recording'] = dataset_seqs
    for i in range(STEPS):
        dataset_info['step_{}'.format(i+1)] = False
    dataset_info['total'] = 0
    dataset_info.to_csv(dp_log_info_file, index=False)
    print('\nDataset size: {}'.format(len(dataset_seqs)))


if __name__ == '__main__':
    sys.exit(main())