#!/bin/bash
# ----------------------------------------------------------------------------------
# This script runs to compute monocular depth from the RGB images of the DAVIDE dataset.
# It requires a CLIP_ID to specify which video to process.
# Optional arguments include a custom config file.
# ----------------------------------------------------------------------------------
# Usage: bash ./scripts/run_07_mono_depth.sh <CLIP_ID> [--config <CONFIG_FILE>]
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

# Run the monocular depth estimation for both sharp and blurred images
python davide_dp/mono_depth.py --id $CLIP_ID --config $CONFIG --rgb_dir sharp
python davide_dp/mono_depth.py --id $CLIP_ID --config $CONFIG --rgb_dir blur