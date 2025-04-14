#!/bin/bash
# ---------------------------------------------------------------------------------
# This script extracts RGB frames from the raw video captures of the DAVIDE dataset.
# It requires a CLIP_ID to specify which video to process.
# Optional arguments include a custom config file.
# ----------------------------------------------------------------------------------
# Usage: bash ./scripts/run_01_extract_rgb.sh <CLIP_ID> [--config <CONFIG_FILE>]
# ----------------------------------------------------------------------------------

# Set Clip ID
CLIP_ID=$1
shift 1

# Default values
CONFIG=./davide_dp/configs/config.yaml
STEP=1

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

# Retrive info from the config file
VIDEOS_PATH_LIST=( )
INPUT_ROOT=$(python -c "from davide_dp.configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-raw', 'ROOT')")
OUTPUT_ROOT=$(python -c "from davide_dp.configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'ROOT')")
DP_LOG=$(python -c "from davide_dp.configs import *;retrieve_attribute('$CONFIG', 'DATA-GEN-PARAMS', 'dp_log')")
RGB_DIR=$(python -c "from davide_dp.configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'rgb_folder')")

# Get video clip
VIDEO_LIST=( $(ls $INPUT_ROOT) )
VIDEO=${VIDEO_LIST[$CLIP_ID]}

# Set the input and output paths
INPUT_PATH="$INPUT_ROOT/$VIDEO/vid.mov"
OUTPUT_DIR="$OUTPUT_ROOT/$VIDEO/$RGB_DIR"
mkdir -p $OUTPUT_DIR 
OUTPUT_PATH="$OUTPUT_DIR/%08d.png"

# Extract RGB frames from the video
ffmpeg -y -i $INPUT_PATH -start_number 0 $OUTPUT_PATH 
# ffmpeg -i $INPUT_PATH -start_number 0 -c:v libx264 -crf 0 $OUTPUT_PATH

# Register the Step 1 in the DP log
python davide_dp/update_db.py --dp_log $DP_LOG --recording $VIDEO --step $STEP
echo "RGB extraction for $VIDEO is done"

