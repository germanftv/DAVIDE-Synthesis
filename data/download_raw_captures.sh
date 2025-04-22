#!/usr/bin/env bash
# ---------------------------------------------------------------------------------
# This script downloads the raw captures from the DAVIDE dataset.
# It requires a username and password for authentication.
# The script will download the files to the directory specified by the DATA_WORKSPACE environment variable.
# The script also has an option to clean up the zip files after extraction.
# ---------------------------------------------------------------------------------
# Usage: bash ./data/download_raw_captures.sh <username> <password> [--clean]
# ---------------------------------------------------------------------------------

# Check if DATA_WORKSPACE is set
if [ -z "$DATA_WORKSPACE" ]; then
  echo "Error: DATA_WORKSPACE environment variable is not set."
  exit 1
fi


USERNAME="$1"
PASSWORD="$2"
shift 2  # Shift arguments so we can check for --clean

CLEAN=false
if [ "$1" = "--clean" ]; then
  CLEAN=true
fi

# Create and switch to the workspace directory
mkdir -p "$DATA_WORKSPACE"
cd "$DATA_WORKSPACE"

# Raw capture links
davide_raw00="https://davide.rd.tuni.fi/raw-captures/DAVIDE-raw.z01"
davide_raw01="https://davide.rd.tuni.fi/raw-captures/DAVIDE-raw.z02"
davide_raw02="https://davide.rd.tuni.fi/raw-captures/DAVIDE-raw.z03"
davide_raw03="https://davide.rd.tuni.fi/raw-captures/DAVIDE-raw.z04"
davide_raw04="https://davide.rd.tuni.fi/raw-captures/DAVIDE-raw.zip"

# Download the raw captures
curl -u "${USERNAME}:${PASSWORD}" -O "${davide_raw00}"
curl -u "${USERNAME}:${PASSWORD}" -O "${davide_raw01}"
curl -u "${USERNAME}:${PASSWORD}" -O "${davide_raw02}"
curl -u "${USERNAME}:${PASSWORD}" -O "${davide_raw03}"
curl -u "${USERNAME}:${PASSWORD}" -O "${davide_raw04}"

# Unzip the raw captures
zip -s 0 DAVIDE-raw.zip --out DAVIDE-raw_combined.zip
unzip DAVIDE-raw_combined.zip

# Optionally remove the zip files
if [ "$CLEAN" = true ]; then
  rm DAVIDE-raw.z01
  rm DAVIDE-raw.z02
  rm DAVIDE-raw.z03
  rm DAVIDE-raw.z04
  rm DAVIDE-raw.zip
  rm DAVIDE-raw_combined.zip
fi

# Download license file
curl -u "${USERNAME}:${PASSWORD}" -O "https://davide.rd.tuni.fi/raw-captures/LICENSE.txt"