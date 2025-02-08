#!/bin/bash

# Function to cleanup on exit
cleanup() {
    echo -e "\nCleaning up..."
    
    # Kill any running Gweeb processes
    pkill -f "python.*gweeb.py" 2>/dev/null
    
    # If we created/activated a venv, deactivate it
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null
    fi
    
    echo "Cleanup complete. Goodbye!"
    exit 0
}

# Register cleanup function to run on script exit
trap cleanup EXIT INT TERM

echo "Setting up Gweeb environment..."

# Check if Python 3.8+ is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}")')
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

# Check version is at least 3.8
if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 8 ]); then
    echo "Python 3.8 or higher is required. Found version $PYTHON_VERSION"
    exit 1
fi

echo "Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements if needed
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOF
PySide6==6.8.2
zeroconf==0.131.0
cryptography==43.0.1
psutil==5.9.8
EOF
fi

echo "Installing requirements..."
pip install -r requirements.txt

# Run Gweeb
echo "Starting Gweeb..."
python gweeb.py

# Note: Cleanup will be handled by the cleanup function on exit 