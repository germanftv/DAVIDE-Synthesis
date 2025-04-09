#!/bin/bash
#SBATCH --job-name=CAM_DATA
# slurm logs
#SBATCH --output=logs/s05/log_%a.txt
#SBATCH --error=logs/s05/log_%a.txt
#
#SBATCH --partition=small
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=10000
#SBATCH --array=0-92

module load ffmpeg
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ..
srun bash run_05_camera_data.sh