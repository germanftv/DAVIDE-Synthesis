#!/bin/bash
#SBATCH --job-name=Export-DAVIDE
# slurm logs
#SBATCH --output=logs/s08/log_%a.txt
#SBATCH --error=logs/s08/log_%a.txt
# slurm settings
#SBATCH --partition=small
#SBATCH --time=00:20:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16000
#SBATCH --array=0-92

# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ..
srun bash scripts/run_08_data_selection.sh $SLURM_ARRAY_TASK_ID --config ./davide_dp/configs/config.yaml