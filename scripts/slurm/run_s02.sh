#!/bin/bash
#SBATCH --job-name=XVFI
# slurm logs
#SBATCH --output=logs/s02/log_%a.txt
#SBATCH --error=logs/s02/log_%a.txt
#
#SBATCH --partition=gpu
#SBATCH --time=08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=16000
#SBATCH --gres=gpu:v100:1,nvme:16
#SBATCH --array=0-92

# Load CUDA
module load cuda
# Activate enviroment, export variables
source ~/env_vars/XVFI.sh

cd ..
srun bash run_02_VFI.sh