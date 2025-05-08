#!/bin/bash
#SBATCH --job-name=Extract-RGB
# slurm logs
#SBATCH --output=logs/s01/log_%a.txt
#SBATCH --error=logs/s01/log_%a.txt
# slurm settings
#SBATCH --partition=small
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16000
#SBATCH --array=0-92

# Load ffmpeg
module load ffmpeg
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ../..
srun bash scripts/run_01_extract_rgb.sh $SLURM_ARRAY_TASK_ID --config ./davide_dp/configs/config.yaml