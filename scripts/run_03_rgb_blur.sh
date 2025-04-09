#!/bin/bash
cd ..
CONFIG=./configs/config.yaml

python rgb_blur.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID