#!/bin/bash
#SBATCH --job-name=VID2RGB
# slurm logs
#SBATCH --output=logs/s01/log_%a.txt
#SBATCH --error=logs/s01/log_%a.txt
#
#SBATCH --partition=small
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16000
#SBATCH --array=0-92

# Load ffmpeg
module load ffmpeg
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ..
srun bash run_01_extract_rgb.sh