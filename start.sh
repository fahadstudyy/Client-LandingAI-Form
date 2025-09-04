#!/bin/bash

# Exit if any command fails
set -e

# Activate the venv
source "$(dirname "$0")/venv/bin/activate"

# Run the Python module
python -m app