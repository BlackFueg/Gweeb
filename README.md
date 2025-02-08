# Gweeb

A lightweight LAN clipboard sharing utility that lives in your system tray.

## Features
- Share clipboard text between machines on the same LAN
- Simple system tray interface
- Automatic device discovery using Zeroconf
- Instant notifications for received clips
- Works on macOS and Windows
- Background app that stays out of your way
- Secure communication over ZeroTier virtual networks (recommended)
- Also works on regular LANs

## Potential Uses

### Development & Debugging
- Share console logs between development and testing machines
- Quickly transfer error messages from headless servers to development machines
- Copy-paste build commands across multiple development environments
- Share Git commands or commit hashes between machines

### DevOps & System Administration
- Distribute configuration snippets across multiple servers
- Share terminal commands for simultaneous system updates
- Copy long SSH keys or authentication tokens between machines
- Transfer log entries or system outputs for troubleshooting

### Cross-Platform Development
- Share test data between different platform builds
- Copy platform-specific commands between development environments
- Transfer build outputs between compilation environments

### Content Creation & Design
- Share color codes between design tools
- Transfer CSS/HTML snippets between mockup and development machines
- Copy metadata or file paths between editing stations
- Share script snippets between recording/streaming setups

### Security & Network Testing
- Share network scan results between analysis machines
- Transfer configuration snippets between test environments
- Copy long encryption keys or certificates between systems
- Share packet capture data between analysis tools

### General Productivity
- Copy-paste meeting notes between work and personal devices
- Share URLs between machines without email/messaging
- Transfer configuration settings across workstations
- Quick sharing of temporary credentials in secure environments

## Installation

### macOS
1. Download the repository
2. Run the installer:
   ```bash
   ./install.sh
   ```
   This will:
   - Install all necessary dependencies (Homebrew, Python, etc.)
   - Set up Gweeb in your Applications folder
   - Add a `gweeb` command to your shell

### Windows
1. Download the repository
2. Run the installer:
   ```bash
   install.bat
   ```

### Linux (BETA)
> ⚠️ **Note**: Linux support is currently in BETA and may have issues. Please report any problems you encounter.

1. Download the repository
2. Run the installer:
   ```bash
   ./install_linux.sh
   ```
   This will:
   - Install required system packages and Python dependencies
   - Set up Gweeb in your user directory
   - Add a desktop entry and command-line launcher

#### Linux Requirements
- Ubuntu 22.04 or similar (other distributions may work but are untested)
- Python 3.8 or higher
- System tray support:
  - For GNOME: Install "KStatusNotifierItem/AppIndicator Support" extension
  - For KDE: Should work out of the box
- D-Bus for native notifications (optional)

#### Known Linux Issues
- System tray icon may not appear in some desktop environments
- Notifications might fall back to Qt-based popups if D-Bus is not available
- Some window managers may need additional configuration for proper tray support

## Usage
1. Launch Gweeb:
   - macOS: Type `gweeb` in terminal or run `~/Applications/Gweeb/launch_gweeb.sh`
   - Windows: Run Gweeb from the Start Menu
2. The app will appear in your system tray (menu bar on macOS)
3. Devices on the same network will automatically discover each other
4. Copy text on one machine to share it with others
5. Click the system tray icon to:
   - View clipboard history
   - Send specific text
   - Configure settings
   - View connected devices

## Requirements
- macOS 10.15+ or Windows 10+
- Machines must be on the same network (either physical LAN or virtual)
- ZeroTier (recommended):
  - For secure communication across different networks
  - For connecting machines behind different NATs
  - Download from [zerotier.com](https://www.zerotier.com)

## Network Configuration
Gweeb works in two modes:
1. **ZeroTier Mode (Recommended)**:
   - Install ZeroTier on all machines
   - Join the same ZeroTier network
   - Gweeb will automatically prefer ZeroTier interfaces
   - Secure communication across any network

2. **Local Network Mode**:
   - No additional setup required
   - Machines must be on the same local network
   - Less secure, only recommended for trusted networks
   - May not work across different subnets

## Troubleshooting

### Windows
1. **Devices not discovering each other**:
   - Ensure all machines are on the same network
   - Check Windows Firewall settings for Python/Gweeb
   - If using ZeroTier, verify all machines show "OK" status

### macOS
1. **Installation issues**:
   - Ensure Homebrew is installed
   - Check system requirements are met
   - Make sure you have write permissions to ~/Applications

### Linux (BETA)
1. **System tray icon not showing**:
   - GNOME users: Install "KStatusNotifierItem/AppIndicator Support" extension
   - Verify your desktop environment supports system tray icons
   - Try restarting your session

2. **Notifications not working**:
   - Install `python3-dbus` package: `sudo apt install python3-dbus`
   - Check if D-Bus is running: `systemctl --user status dbus`
   - App will fall back to Qt notifications if D-Bus is unavailable

3. **Installation issues**:
   - Run `sudo apt install python3-venv python3-pip` if not already installed
   - Check if Qt dependencies are installed
   - Ensure ~/.local/bin is in your PATH

## Development
To set up a development environment:
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python gweeb.py
   ```

## License
MIT License - Copyright (c) 2024 Valkyrie Innovation - See LICENSE file for details 