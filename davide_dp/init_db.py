import os
import sys
import argparse
import pandas as pd

from davide_dp.utils import create_tables, initialize_summary_from_raw_list
from configs.utils import read_config


def arg_parser():
    parser = argparse.ArgumentParser(description='Initialize the database for the data synthesis pipeline')
    parser.add_argument('--config', type=str, default='davide_dp/configs/config.yaml', help='Path to the configuration file')
    args = parser.parse_args()
    return args


def main():
    # Parse command-line arguments
    args = arg_parser()

    # Check configuration file
    if args.config is None:
        print('Please provide a configuration file.')
        sys.exit(1)
    if not os.path.exists(args.config):
        print(f'Configuration file {args.config} does not exist.')
        sys.exit(1)
    
    # Load configurations
    config = read_config(args.config)
    dp_path = config['DATA-GEN-PARAMS']['dp_log']
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']

    # Get the list of raw files
    annotations = pd.read_csv(data_annotations_path)
    raw_list = annotations['recording'].values.tolist()
    
    # Initialize the database
    create_tables(dp_path)
    initialize_summary_from_raw_list(raw_list, dp_path)
    print('Database initialized.')


if __name__ == '__main__':
    main()