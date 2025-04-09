#!/bin/bash
#SBATCH --job-name=DEPTH
# slurm logs
#SBATCH --output=logs/s04/log_%a.txt
#SBATCH --error=logs/s04/log_%a.txt
#
#SBATCH --partition=small
#SBATCH --time=00:14:50
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=12000
#SBATCH --array=0-92

# Activate enviroment, export variables
source ~/env_vars/DAVIDE-DP.sh

cd ..
srun bash run_04_depth.sh