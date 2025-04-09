#!/bin/bash
#SBATCH --job-name=DATA-SEL
# slurm logs
#SBATCH --output=logs/s08/log_%a.txt
#SBATCH --error=logs/s08/log_%a.txt
#
#SBATCH --partition=small
#SBATCH --time=00:20:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16000
#SBATCH --array=0-92

# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ..
srun bash run_08_data_selection.sh