#!/bin/bash
cd ..
CONFIG=./configs/config.yaml

python depth.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID