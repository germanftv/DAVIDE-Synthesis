#!/bin/bash
#SBATCH --job-name=Extract-CameraData
# slurm logs
#SBATCH --output=logs/s05/log_%a.txt
#SBATCH --error=logs/s05/log_%a.txt
# slurm settings
#SBATCH --partition=small
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=10000
#SBATCH --array=0-92

module load ffmpeg
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ../..
srun bash scripts/run_05_camera_data.sh $SLURM_ARRAY_TASK_ID --config ./davide_dp/configs/config.yaml