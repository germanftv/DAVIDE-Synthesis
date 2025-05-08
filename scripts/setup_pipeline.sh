#!/bin/bash
# ---------------------------------------------------------------------------------
# This script sets up the pipeline for data processing.
# It initializes the database and prepares the workspace for data processing.
# It requires a path to set DATA_WORKSPACE environment variable, which specifies where the data will be stored.
# Optional arguments include --init_db to initialize the database and --config to specify a custom config file.
# Note: The database intends to log the processing steps. The database is initialized
#       based on the annotations file provided in the config file.
# ----------------------------------------------------------------------------------
# Usage: bash ./scripts/setup_pipeline.sh <DATA_WORKSPACE_PATH> [--config <CONFIG_FILE>] [--init_db]
# ----------------------------------------------------------------------------------

# Set DATA_WORKSPACE
DATA_WORKSPACE_PATH=$1
shift 1
echo "DATA_WORKSPACE: $DATA_WORKSPACE_PATH"

# Test conda activation
if ! conda activate DAVIDE-DP; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# Install davide_dp python package
conda activate DAVIDE-DP
pip install -e .
conda deactivate

conda activate DAVIDE-MONO
pip install -e .
conda deactivate

# Check if the DATA_WORKSPACE_PATH is provided
if [ -z "$DATA_WORKSPACE_PATH" ]; then
  echo "Error: DATA_WORKSPACE_PATH is not provided."
  exit 1
fi
# Check if the DATA_WORKSPACE_PATH directory exists
if [ ! -d "$DATA_WORKSPACE_PATH" ]; then
  echo "Error: DATA_WORKSPACE_PATH directory $DATA_WORKSPACE_PATH does not exist."
  exit 1
fi

# Export the DATA_WORKSPACE environment variable
conda activate DAVIDE-DP
conda env config vars set DATA_WORKSPACE=$DATA_WORKSPACE_PATH
echo "DATA_WORKSPACE set to $DATA_WORKSPACE_PATH in the DAVIDE-DP environment."
conda deactivate

conda activate DAVIDE-MONO
conda env config vars set DATA_WORKSPACE=$DATA_WORKSPACE_PATH
echo "DATA_WORKSPACE set to $DATA_WORKSPACE_PATH in the DAVIDE-MONO environment."
conda deactivate

# Check if the --config argument is provided
if [ "$1" == "--config" ]; then
  CONFIG=$2
  shift 2
else
  CONFIG=./davide_dp/configs/config.yaml
fi

# Check if the --init_db argument is provided
if [ "$1" == "--init_db" ]; then
  # Initialize the database
  conda activate DAVIDE-DP
  python davide_dp/init_db.py --config $CONFIG
  if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize the database."
    exit 1
  fi
fi

echo "Pipeline setup completed successfully."
echo "You can now run the data processing scripts."