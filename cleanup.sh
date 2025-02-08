#!/bin/bash

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

# Kill any running Gweeb processes
print_status "Stopping any running Gweeb instances..."
pkill -f "python.*gweeb.py" 2>/dev/null

# List of directories to remove
DIRS_TO_REMOVE=(
    "build"
    "dist"
    "__pycache__"
    "*.egg-info"
    ".pytest_cache"
    ".coverage"
    "venv"
)

# Remove each directory
for dir in "${DIRS_TO_REMOVE[@]}"; do
    if ls -d $dir 2>/dev/null; then
        print_status "Removing $dir..."
        rm -rf $dir
    fi
done

# Remove spec files
print_status "Removing spec files..."
rm -f *.spec

# Remove any .pyc files
print_status "Removing Python cache files..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

print_status "Cleanup complete! Only the essential files remain." 