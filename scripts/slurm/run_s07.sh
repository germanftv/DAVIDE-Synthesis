#!/bin/bash
#SBATCH --job-name=MONO-DEPTH
# slurm logs
#SBATCH --output=logs/s07/log_%a.txt
#SBATCH --error=logs/s07/log_%a.txt
#
#SBATCH --partition=gpu
#SBATCH --time=14:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16000
#SBATCH --gres=gpu:v100:1
#SBATCH --array=0-92

# Load CUDA
module load cuda
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-MONO.sh

cd ..
srun bash run_07_mono_depth.sh