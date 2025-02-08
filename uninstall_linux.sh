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
    print_error "Please do not run this script with sudo."
    exit 1
fi

print_status "Starting Gweeb uninstallation..."

# Confirm uninstallation
echo "This will completely remove Gweeb from your system:"
echo " - Remove the application from ~/.local/share/gweeb"
echo " - Remove the desktop entry"
echo " - Remove the 'gweeb' command"
echo " - Stop any running instances"
echo
read -p "Are you sure you want to uninstall Gweeb? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo
    print_status "Uninstallation cancelled."
    exit 1
fi
echo

# Kill any running instances
print_status "Stopping Gweeb..."
pkill -f "python.*gweeb.py" 2>/dev/null

# Remove launcher script
print_status "Removing 'gweeb' command..."
rm -f "$HOME/.local/bin/gweeb"

# Remove desktop entry
print_status "Removing desktop entry..."
rm -f "$HOME/.local/share/applications/gweeb.desktop"

# Remove application directory
APP_DIR="$HOME/.local/share/gweeb"
if [ -d "$APP_DIR" ]; then
    print_status "Removing application files..."
    
    # Deactivate virtual environment if it exists
    if [ -f "$APP_DIR/venv/bin/deactivate" ]; then
        source "$APP_DIR/venv/bin/deactivate" 2>/dev/null
    fi
    
    # Remove the directory
    rm -rf "$APP_DIR"
    if [ $? -ne 0 ]; then
        print_error "Failed to remove application directory"
        print_error "You may need to close any running instances of Gweeb"
        print_error "and remove the directory manually from: $APP_DIR"
        exit 1
    fi
fi

# Clean up PATH addition if it exists
if [ -f "$HOME/.bashrc" ]; then
    sed -i '/export PATH="$HOME\/.local\/bin:\$PATH"/d' "$HOME/.bashrc"
fi
if [ -f "$HOME/.zshrc" ]; then
    sed -i '/export PATH="$HOME\/.local\/bin:\$PATH"/d' "$HOME/.zshrc"
fi

echo
print_status "Uninstallation complete!"
print_status "Gweeb has been removed from your system."
print_warning "Please restart your terminal or source your shell config to update PATH" 