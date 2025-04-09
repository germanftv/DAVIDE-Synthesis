#!/bin/bash
#SBATCH --job-name=SAMPLE-VID
# slurm logs
#SBATCH --output=logs/s06/log_%a.txt
#SBATCH --error=logs/s06/log_%a.txt
#
#SBATCH --partition=small
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16000
#SBATCH --array=0-92

# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh
# Load modules
module load ffmpeg
module load texlive/texlive

cd ..
srun bash run_06_sample-videos.sh