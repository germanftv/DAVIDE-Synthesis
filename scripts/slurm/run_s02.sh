#!/bin/bash
#SBATCH --job-name=Run-VFI
# slurm logs
#SBATCH --output=logs/s02/log_%a.txt
#SBATCH --error=logs/s02/log_%a.txt
# slurm settings
#SBATCH --partition=gpu
#SBATCH --time=10:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=16000
#SBATCH --gres=gpu:v100:1
#SBATCH --array=0-92

# Load CUDA
module load cuda
# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ../..
srun bash scripts/run_02_VFI.sh $SLURM_ARRAY_TASK_ID --config ./davide_dp/configs/config.yaml