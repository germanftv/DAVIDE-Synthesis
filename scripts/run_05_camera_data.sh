#!/bin/bash
cd ..
CONFIG=./configs/config.yaml

python camera_data.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID