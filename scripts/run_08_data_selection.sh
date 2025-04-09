#!/bin/bash
cd ..
CONFIG=./configs/config.yaml

python data_selection.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID