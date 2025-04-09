#!/bin/bash
cd ..

CONFIG=./configs/config.yaml
STEP=1

VIDEOS_PATH_LIST=( )
INPUT_ROOT=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-raw', 'ROOT')")
OUTPUT_ROOT=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'ROOT')")
DP_LOG=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DATA-GEN-PARAMS', 'dp_log')")
RGB_DIR=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'rgb_folder')")
VIDEO_LIST=( $(ls $INPUT_ROOT) )
VIDEO=${VIDEO_LIST[$SLURM_ARRAY_TASK_ID]}

INPUT_PATH="$INPUT_ROOT/$VIDEO/vid.mov"
OUTPUT_DIR="$OUTPUT_ROOT/$VIDEO/$RGB_DIR"
mkdir -p $OUTPUT_DIR 
OUTPUT_PATH="$OUTPUT_DIR/%08d.png"

ffmpeg -i $INPUT_PATH -start_number 0 $OUTPUT_PATH 
# ffmpeg -i $INPUT_PATH -start_number 0 -c:v libx264 -crf 0 $OUTPUT_PATH


echo "RGB extraction for $VIDEO is done"
python -m utils.update_dp_log --info_log $DP_LOG --recording $VIDEO --step $STEP

