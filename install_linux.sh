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

# Check if script is run with sudo
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script with sudo. It will ask for permissions when needed."
    exit 1
fi

print_status "Starting Gweeb installation..."

# Check for required packages
print_status "Checking system requirements..."
PACKAGES_TO_INSTALL=()

# Check Python
if ! command -v python3 &>/dev/null; then
    PACKAGES_TO_INSTALL+=("python3")
    PACKAGES_TO_INSTALL+=("python3-pip")
    PACKAGES_TO_INSTALL+=("python3-venv")
fi

# Check for required system packages
if ! command -v curl &>/dev/null; then
    PACKAGES_TO_INSTALL+=("curl")
fi

# Qt dependencies for PySide6
PACKAGES_TO_INSTALL+=(
    "libxcb-xinerama0"
    "libxkbcommon-x11-0"
    "libdbus-1-3"
    "libxcb-icccm4"
    "libxcb-image0"
    "libxcb-keysyms1"
    "libxcb-randr0"
    "libxcb-render-util0"
    "libxcb-shape0"
    "libxcb-xfixes0"
)

# Install required packages if any
if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
    print_status "Installing required packages..."
    echo "The following packages will be installed:"
    printf '%s\n' "${PACKAGES_TO_INSTALL[@]}"
    echo
    sudo apt-get update
    sudo apt-get install -y "${PACKAGES_TO_INSTALL[@]}"
fi

# Verify Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    print_error "Python version $PYTHON_VERSION is too old. Gweeb requires Python 3.8 or higher."
    exit 1
fi

# Create application directory
APP_DIR="$HOME/.local/share/gweeb"
if [ ! -d "$APP_DIR" ]; then
    print_status "Creating application directory..."
    mkdir -p "$APP_DIR"
fi

# Copy current directory contents to application directory
if [ "$(pwd)" != "$APP_DIR" ]; then
    print_status "Installing Gweeb to $APP_DIR..."
    cp -R . "$APP_DIR/"
    cd "$APP_DIR" || exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create launcher script
print_status "Creating launcher script..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/gweeb" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/gweeb" || exit 1
source venv/bin/activate
exec python gweeb.py
EOF

chmod +x "$HOME/.local/bin/gweeb"

# Add .local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    print_status "Adding ~/.local/bin to PATH..."
    if [ -f "$HOME/.bashrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
    print_warning "Please restart your terminal or source your shell config to update PATH"
fi

# Create desktop entry
print_status "Creating desktop entry..."
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/gweeb.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Gweeb
Comment=LAN Clipboard Sharing Utility
Exec=$HOME/.local/bin/gweeb
Terminal=false
Categories=Utility;
StartupWMClass=Gweeb
EOF

print_status "Installation complete!"
print_status "You can now run Gweeb by:"
echo "1. Using the 'gweeb' command in terminal (after restarting terminal)"
echo "2. Launching from your applications menu"

# Ask if user wants to run Gweeb now
read -p "Would you like to run Gweeb now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting Gweeb..."
    python gweeb.py
fi 