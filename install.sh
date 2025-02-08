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

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    echo -e "\nCleaning up..."
    
    # Kill any running ClipHop processes
    pkill -f "python.*cliphop.py" 2>/dev/null
    
    # If we created/activated a venv, deactivate it
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null
    fi
    
    echo "Cleanup complete. Goodbye!"
    exit 0
}

# Register cleanup function to run on script exit
trap cleanup EXIT INT TERM

# Check if script is run with sudo
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script with sudo. It will ask for permissions when needed."
    exit 1
fi

print_status "Starting ClipHop installation..."

# Check for Command Line Tools
if ! xcode-select -p &>/dev/null; then
    print_status "Installing Command Line Tools..."
    xcode-select --install
    print_status "Please wait for Command Line Tools installation to complete and press Enter to continue..."
    read -r
fi

# Check for Homebrew
if ! command -v brew &>/dev/null; then
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    print_status "Updating Homebrew..."
    brew update
fi

# Install Python if needed
if ! command -v python3 &>/dev/null; then
    print_status "Installing Python..."
    brew install python@3.11
else
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
        print_status "Upgrading Python..."
        brew install python@3.11
    fi
fi

# Ensure pip is installed
if ! command -v pip3 &>/dev/null; then
    print_status "Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Create application directory if it doesn't exist
APP_DIR="$HOME/Applications/ClipHop"
if [ ! -d "$APP_DIR" ]; then
    print_status "Creating application directory..."
    mkdir -p "$APP_DIR"
fi

# Copy current directory contents to application directory if needed
if [ "$(pwd)" != "$APP_DIR" ]; then
    print_status "Installing ClipHop to $APP_DIR..."
    cp -R . "$APP_DIR/"
    cd "$APP_DIR" || exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip in virtual environment
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Ensure requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_status "Creating requirements.txt..."
    cat > requirements.txt << EOF
PySide6==6.8.2
zeroconf==0.131.0
cryptography==43.0.1
psutil==5.9.8
EOF
fi

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create a launcher script
print_status "Creating launcher script..."
cat > "$HOME/Applications/ClipHop/launch_cliphop.sh" << 'EOF'
#!/bin/bash

# Change to the ClipHop directory
cd "$HOME/Applications/ClipHop" || exit 1

# Activate virtual environment
source venv/bin/activate

# Run ClipHop
python cliphop.py
EOF

chmod +x "$HOME/Applications/ClipHop/launch_cliphop.sh"

# Create an alias in .zshrc if it doesn't exist
if ! grep -q "alias cliphop=" "$HOME/.zshrc" 2>/dev/null; then
    print_status "Adding 'cliphop' command to shell..."
    echo "alias cliphop='$HOME/Applications/ClipHop/launch_cliphop.sh'" >> "$HOME/.zshrc"
    print_warning "Please restart your terminal or run 'source ~/.zshrc' to use the 'cliphop' command"
fi

print_status "Installation complete!"
print_status "You can now run ClipHop by:"
echo "1. Using the 'cliphop' command in terminal (after restarting terminal)"
echo "2. Running '$HOME/Applications/ClipHop/launch_cliphop.sh'"

# Ask if user wants to run ClipHop now
read -p "Would you like to run ClipHop now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting ClipHop..."
    python cliphop.py
fi 