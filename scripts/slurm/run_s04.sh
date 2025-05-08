#!/bin/bash
#SBATCH --job-name=Extract-Depth
# slurm logs
#SBATCH --output=logs/s04/log_%a.txt
#SBATCH --error=logs/s04/log_%a.txt
# slrum settings
#SBATCH --partition=small
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=12000
#SBATCH --array=0-92

# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ../..
srun bash scripts/run_04_depth.sh $SLURM_ARRAY_TASK_ID --config ./davide_dp/configs/config.yaml