#!/bin/bash
cd ..

CONFIG=./configs/config.yaml

python VFI_runner.py --config $CONFIG --id $SLURM_ARRAY_TASK_ID