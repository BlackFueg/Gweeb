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
1. **Devices not discovering each other**:
   - Ensure all machines are on the same network
   - Check firewall settings for Python/Gweeb
   - If using ZeroTier, verify all machines show "OK" status

2. **Text not sending**:
   - Check if auto-send is enabled in the tray menu
   - Verify network connectivity between machines
   - Look for any firewall blocking messages

3. **Installation issues**:
   - Windows: Run installer without admin privileges
   - macOS: Ensure Homebrew is installed
   - Check system requirements are met

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