#!/bin/bash
cd ..
CONFIG=./configs/config.yaml

python mono_depth.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID --rgb_dir sharp
python mono_depth.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID --rgb_dir blur