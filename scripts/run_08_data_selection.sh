#!/bin/bash
# ----------------------------------------------------------------------------------
# This script exports the processed data from the DAVIDE dataset.
# It requires a CLIP_ID to specify which video to process.
# Optional arguments include a custom config file.
# ----------------------------------------------------------------------------------
# Usage: bash ./scripts/run_08_data_selection.sh <CLIP_ID> [--config <CONFIG_FILE>]
# ----------------------------------------------------------------------------------

# Set Clip ID
CLIP_ID=$1
shift 1

# Default config file
CONFIG=./davide_dp/configs/config.yaml

# Parse optional --config argument
if [ "$1" == "--config" ]; then
  CONFIG=$2
  shift 2
fi

# Check if the config file exists
if [ ! -f "$CONFIG" ]; then
  echo "Error: Config file $CONFIG not found."
  exit 1
fi

# Check if the CLIP_ID is provided
if [ -z "$CLIP_ID" ]; then
  echo "Error: CLIP_ID is not provided."
  exit 1
fi

python davide_dp/data_selection.py --id $CLIP_ID --config $CONFIG