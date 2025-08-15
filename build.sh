#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for dlib
apt-get update && apt-get install -y build-essential cmake

# Install Python dependencies
pip install -r requirements.txt