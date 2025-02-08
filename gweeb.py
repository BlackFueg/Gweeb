import sys
import random
import string
import socket
import json
import os
import signal
import atexit
import psutil
import platform
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                            QVBoxLayout, QTextEdit, QPushButton, QInputDialog,
                            QLineEdit, QMessageBox, QListWidget, QListWidgetItem,
                            QHBoxLayout)
from PySide6.QtGui import QIcon, QPixmap, QImage, QCursor, QClipboard
from PySide6.QtCore import Qt, QObject, Signal, QThread, QTimer
import threading
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceStateChange
import socket
import time

# Global flag for cleanup
_cleanup_done = False
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# For Linux desktop notifications
if IS_LINUX:
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        HAVE_DBUS = True
    except ImportError:
        HAVE_DBUS = False
        print("Warning: dbus-python not installed, falling back to Qt notifications")

def get_local_ip():
    """Get the local IP address that can be used for LAN communication"""
    if IS_WINDOWS:
        try:
            # Windows-specific approach using ipconfig
            import subprocess
            output = subprocess.check_output("ipconfig", shell=True).decode()
            for line in output.split('\n'):
                if "IPv4 Address" in line:
                    ip = line.split(": ")[-1].strip()
                    if ip.startswith('172.26.'):
                        print(f"Found zerotier interface with IP: {ip}")
                        return ip
            
            # If no zerotier interface found, use first non-loopback interface
            for line in output.split('\n'):
                if "IPv4 Address" in line:
                    ip = line.split(": ")[-1].strip()
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        print(f"Found non-loopback interface with IP: {ip}")
                        return ip
        except Exception as e:
            print(f"Windows ipconfig method failed: {e}")
    else:
        try:
            # macOS/Linux approach using netifaces
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip.startswith('172.26.'):  # Match zerotier subnet
                            print(f"Found zerotier interface {interface} with IP: {ip}")
                            return ip
            
            # Try all interfaces if no zerotier found
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            print(f"Found non-loopback interface {interface} with IP: {ip}")
                            return ip
        except ImportError:
            print("netifaces not available, falling back to socket method")
    
    # Fallback to socket method
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            print(f"Found IP using socket method: {local_ip}")
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
        return local_ip
    except Exception as e:
        print(f"Socket method failed: {e}")
        # Final fallback
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        print(f"Using hostname method, found IP: {ip}")
        return ip

def is_valid_interface(ip):
    """Check if the IP is on our zerotier network"""
    return ip.startswith('172.26.')

def force_kill_process(pid):
    """Force kill a process and all its children"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                if IS_WINDOWS:
                    child.kill()
                else:
                    os.kill(child.pid, signal.SIGKILL)
            except:
                pass
        if IS_WINDOWS:
            parent.kill()
        else:
            os.kill(pid, signal.SIGKILL)
    except:
        pass

def cleanup():
    global _cleanup_done
    if not _cleanup_done:
        print("\nPerforming cleanup...")
        if 'gweeb' in globals():
            try:
                gweeb.force_quit()
            except:
                pass
        
        # Force kill our process and children
        try:
            force_kill_process(os.getpid())
        except:
            pass
        _cleanup_done = True

# Register cleanup handlers
atexit.register(cleanup)
if not IS_WINDOWS:
    signal.signal(signal.SIGTERM, lambda signo, frame: cleanup())
    signal.signal(signal.SIGINT, lambda signo, frame: cleanup())

def show_linux_notification(title, message, timeout=2000):
    """Show a notification using Linux's notification system"""
    if not IS_LINUX or not HAVE_DBUS:
        return False
        
    try:
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        notify = dbus.Interface(
            bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications'),
            'org.freedesktop.Notifications'
        )
        notify.Notify(
            'Gweeb',  # App name
            0,        # Replace ID
            '',      # Icon (empty for default)
            title,
            message,
            [],      # Actions
            {},      # Hints
            timeout  # Timeout in ms
        )
        return True
    except Exception as e:
        print(f"Failed to show Linux notification: {e}")
        return False

def create_icon():
    # Create a simple clipboard icon
    img = QImage(16, 16, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    
    # Draw clipboard outline
    for x in range(16):
        img.setPixelColor(x, 0, Qt.GlobalColor.black)  # Top
        img.setPixelColor(x, 15, Qt.GlobalColor.black)  # Bottom
        if x < 2 or x > 13:
            for y in range(16):
                img.setPixelColor(x, y, Qt.GlobalColor.black)  # Sides
    
    # Draw clip
    for x in range(5, 11):
        img.setPixelColor(x, 2, Qt.GlobalColor.black)
    for y in range(2, 5):
        img.setPixelColor(5, y, Qt.GlobalColor.black)
        img.setPixelColor(10, y, Qt.GlobalColor.black)
    
    return QIcon(QPixmap.fromImage(img))

class DeviceDiscovery(QObject):
    device_found = Signal(str, str, str)  # device_id, ip_address, interface_ip
    device_removed = Signal(str)  # device_id

    def __init__(self):
        super().__init__()
        self.zeroconf = Zeroconf()
        self.browser = None
        self.info = None
        self.local_ip = None
        self.hostname = socket.gethostname()  # Store full hostname for display
        
    def start_advertising(self, device_id, port):
        # Get local IP
        self.local_ip = get_local_ip()
        if not is_valid_interface(self.local_ip):
            print(f"Warning: Using non-zerotier interface: {self.local_ip}")
        print(f"Advertising as {device_id} ({self.hostname}) on interface: {self.local_ip}")
        
        self.info = ServiceInfo(
            "_cliphop._tcp.local.",
            f"{device_id}._cliphop._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=port,
            properties={
                b'device_id': device_id.encode('utf-8'),
                b'hostname': self.hostname.encode('utf-8'),  # Include full hostname
                b'interface': self.local_ip.encode('utf-8')
            }
        )
        self.zeroconf.register_service(self.info)
        
        # Start browsing for other devices
        self.browser = ServiceBrowser(self.zeroconf, "_cliphop._tcp.local.",
                                    handlers=[self._on_service_state_change])
    
    def _on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change is ServiceStateChange.Added or state_change is ServiceStateChange.Updated:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.properties:
                try:
                    device_id = info.properties[b'device_id'].decode('utf-8')
                    hostname = info.properties.get(b'hostname', b'Unknown').decode('utf-8')
                    remote_interface = info.properties[b'interface'].decode('utf-8')
                    if device_id:
                        ip = socket.inet_ntoa(info.addresses[0])
                        if not is_valid_interface(ip):
                            print(f"Warning: Device {device_id} ({hostname}) using non-zerotier interface: {ip}")
                        print(f"Found device {device_id} ({hostname}) at {ip} (interface: {remote_interface})")
                        if is_valid_interface(ip) and is_valid_interface(remote_interface):
                            self.device_found.emit(device_id, ip, remote_interface)
                        else:
                            print(f"Ignoring device {device_id} ({hostname}) due to invalid interface")
                except (KeyError, IndexError, AttributeError) as e:
                    print(f"Error processing service info: {e}")
        elif state_change is ServiceStateChange.Removed:
            # Extract device_id from the service name
            try:
                device_id = name.split('.')[0]
                self.device_removed.emit(device_id)
            except IndexError:
                pass
    
    def stop(self):
        if self.info:
            try:
                self.zeroconf.unregister_service(self.info)
            except:
                pass
        try:
            self.zeroconf.close()
        except:
            pass

class NetworkListener(QThread):
    text_received = Signal(str, str)  # sender_id, text

    def __init__(self, port=5555):
        super().__init__()
        self.interface_ip = get_local_ip()
        if not is_valid_interface(self.interface_ip):
            print(f"Warning: Network listener using non-zerotier interface: {self.interface_ip}")
        self.port = self._find_available_port(port)
        self.running = True
        self.server = None
        print(f"Network listener starting on {self.interface_ip}:{self.port}")

    def _find_available_port(self, start_port):
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.interface_ip, port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError("Could not find an available port")

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((self.interface_ip, self.port))
            print(f"Successfully bound to {self.interface_ip}:{self.port}")
        except Exception as e:
            print(f"Failed to bind to {self.interface_ip}:{self.port}: {e}")
            return

        self.server.settimeout(1)  # 1 second timeout for accept()
        self.server.listen(5)
        print("Server is listening for connections")
        
        while self.running:
            try:
                client, addr = self.server.accept()
                print(f"Accepted connection from {addr}")
                data = client.recv(1024*1024).decode('utf-8')  # Support up to 1MB of text
                if data:
                    try:
                        message = json.loads(data)
                        print(f"Received message from {message.get('sender_id', 'unknown')}")
                        self.text_received.emit(message['sender_id'], message['text'])
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode message: {e}")
                client.close()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only print error if we're still supposed to be running
                    print(f"Error in network listener: {e}")

    def stop(self):
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass

class SendTextDialog(QWidget):
    def __init__(self, parent=None, target_id=None, port=5555, device_id=None, devices=None):
        super().__init__()  # Initialize without parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)  # Set window flags after initialization
        self.setWindowTitle(f"Send Text to {target_id}")
        self.port = port
        self.device_id = device_id
        self.target_id = target_id
        ip, _ = devices.get(target_id, (None, None))  # Get IP for target device
        self.target_ip = ip
        self._parent_ref = parent  # Keep a reference to parent object
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Text input section
        text_section = QVBoxLayout()
        text_label = QLineEdit("Enter text to send:")
        text_label.setReadOnly(True)
        text_label.setFrame(False)
        self.text_edit = QTextEdit()
        text_section.addWidget(text_label)
        text_section.addWidget(self.text_edit)
        
        # Button section
        button_layout = QHBoxLayout()
        paste_button = QPushButton("Paste from Clipboard")
        paste_button.clicked.connect(self.paste_from_clipboard)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_text)
        button_layout.addWidget(paste_button)
        button_layout.addWidget(self.send_button)
        
        # Add all sections to main layout
        layout.addLayout(text_section)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 300)
        
        # Center the dialog on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        self.text_edit.setText(clipboard.text())
        QMessageBox.information(self, "Clipboard", "Text pasted from clipboard!")

    def send_text(self):
        if not self.target_ip:
            QMessageBox.warning(self, "Error", "Target device not found")
            return
            
        text = self.text_edit.toPlainText()
        if not text:
            QMessageBox.warning(self, "Error", "Please enter some text to send")
            return
            
        if not is_valid_interface(self.target_ip):
            QMessageBox.warning(self, "Error", f"Invalid target interface: {self.target_ip}")
            return
            
        print(f"Attempting to send text to {self.target_id} at {self.target_ip}:{self.port}")
            
        try:
            # Create socket bound to the correct interface
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if hasattr(self._parent_ref, 'listener'):
                local_interface = self._parent_ref.listener.interface_ip
                if not is_valid_interface(local_interface):
                    print(f"Warning: Local interface {local_interface} is not valid, attempting to find zerotier interface")
                    local_interface = get_local_ip()
                    if not is_valid_interface(local_interface):
                        QMessageBox.warning(self, "Error", "Could not find valid zerotier interface")
                        return
                
                local_addr = (local_interface, 0)
                client.bind(local_addr)
                print(f"Bound client to local interface: {local_addr[0]}")
            
            client.settimeout(5)
            print(f"Connecting to {self.target_ip}:{self.port}...")
            client.connect((self.target_ip, self.port))
            print("Connected successfully")
            
            message = {
                'sender_id': self.device_id,
                'text': text
            }
            encoded_message = json.dumps(message).encode('utf-8')
            print(f"Sending message of size {len(encoded_message)} bytes")
            client.send(encoded_message)
            print("Message sent successfully")
            client.close()
            QMessageBox.information(self, "Success", "Text sent successfully!")
            self.close()
        except socket.timeout:
            QMessageBox.warning(self, "Error", f"Connection timed out while trying to connect to {self.target_ip}:{self.port}")
        except ConnectionRefusedError:
            QMessageBox.warning(self, "Error", f"Connection refused by {self.target_ip}:{self.port} - Check if the target is running and the port is not blocked by firewall")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send text: {str(e)}\nTarget: {self.target_ip}:{self.port}")

class TextHistoryDialog(QWidget):
    def __init__(self, texts, parent=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("Message History")
        self.texts = texts
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Add list widget to show messages
        self.list_widget = QListWidget()
        for text_entry in reversed(self.texts):  # Show newest first
            if isinstance(text_entry, dict):
                # New format with metadata
                text = text_entry['text']
                sender = text_entry.get('sender_id', 'Unknown')
                timestamp = text_entry.get('timestamp', '')
                display_text = f"[{timestamp}] From {sender}\n\n{text}"  # Add extra newline for clarity
                
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemIsSelectable)
                # Store just the original text for copying
                item.setData(Qt.UserRole, text)
            else:
                # Legacy format (just text)
                item = QListWidgetItem(text_entry)
                item.setFlags(item.flags() | Qt.ItemIsSelectable)
                item.setData(Qt.UserRole, text_entry)
                
            self.list_widget.addItem(item)
        
        # Add copy button
        copy_button = QPushButton("Copy Selected")
        copy_button.clicked.connect(self.copy_selected)
        
        # Add clear button
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        
        # Add buttons to horizontal layout
        button_layout = QVBoxLayout()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(clear_button)
        
        layout.addWidget(QLineEdit("Double-click to copy text:"))
        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(500, 400)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())
        
        # Connect double-click handler
        self.list_widget.itemDoubleClicked.connect(self.copy_item)
    
    def copy_selected(self):
        if self.list_widget.currentItem():
            text = self.list_widget.currentItem().data(Qt.UserRole)
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Copied", "Text copied to clipboard!")
    
    def copy_item(self, item):
        text = item.data(Qt.UserRole)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Text copied to clipboard!")
    
    def clear_history(self):
        reply = QMessageBox.question(self, "Clear History", 
                                   "Are you sure you want to clear all message history?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.texts.clear()
            self.list_widget.clear()

class Gweeb(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.device_id = self.generate_device_id()
        self.paired_devices = {}  # device_id -> (ip_address, interface_ip)
        self.received_texts = []
        self.current_dialog = None
        self.auto_send_enabled = True  # Default to auto-send enabled
        self.auto_receive_enabled = True  # Default to auto-receive enabled
        self._suppress_clipboard_monitoring = False
        self._last_clipboard_check = time.time()
        
        # Store the process ID
        self.pid = os.getpid()
        
        # Write PID to file for cleanup
        if IS_LINUX:
            pid_dir = os.path.expanduser("~/.local/share/gweeb")
        else:
            pid_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(pid_dir, exist_ok=True)
        self.pid_file = os.path.join(pid_dir, 'gweeb.pid')
        with open(self.pid_file, 'w') as f:
            f.write(str(self.pid))
        
        # Create system tray icon
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip('Gweeb')
        
        # Set icon
        self.tray.setIcon(create_icon())
        
        # Create tray menu
        self.menu = QMenu()
        self.setup_menu()
        self.tray.setContextMenu(self.menu)
        
        # Connect the tray icon's activated signal
        if IS_LINUX:
            # On Linux, show menu for any click
            self.tray.activated.connect(lambda reason: self.menu.popup(QCursor.pos()))
        else:
            # On other platforms, use default behavior
            self.tray.activated.connect(self.show_menu)
        
        # Start network listener first to get the interface
        self.listener = NetworkListener()
        self.listener.text_received.connect(self.handle_received_text)
        self.listener.start()
        
        # Start device discovery with the same interface
        self.discovery = DeviceDiscovery()
        self.discovery.device_found.connect(self.handle_device_found)
        self.discovery.device_removed.connect(self.handle_device_removed)
        self.discovery.start_advertising(self.device_id, self.listener.port)
        
        # Show the tray icon
        if not self.tray.isSystemTrayAvailable():
            if IS_LINUX:
                print("Warning: System tray not available. Please ensure you have a system tray installed.")
                print("For Gnome, you might need the 'KStatusNotifierItem/AppIndicator Support' extension.")
            QMessageBox.warning(None, "System Tray",
                              "System tray is not available on this system!")
        self.tray.show()
        
        # Set up clipboard monitoring with timer
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.handle_clipboard_change)
        self.last_clipboard_text = self.clipboard.text()  # Store initial clipboard content
        
        # Create a timer to periodically check clipboard
        self._clipboard_timer = QTimer()
        self._clipboard_timer.timeout.connect(self.check_clipboard)
        self._clipboard_timer.start(1000)  # Check every second

    def generate_device_id(self):
        """Generate a device ID based on the machine's hostname."""
        hostname = socket.gethostname()
        # Clean up hostname - remove special characters and limit length
        clean_hostname = ''.join(c for c in hostname if c.isalnum() or c in '-_')
        # Truncate if too long (keeping it reasonable for display)
        if len(clean_hostname) > 20:
            clean_hostname = clean_hostname[:20]
        return clean_hostname.upper()  # Convert to uppercase for consistency

    def show_menu(self, reason):
        # On macOS, only show the menu for left clicks to avoid duplicate menus
        if IS_WINDOWS or reason == QSystemTrayIcon.Trigger:  # Trigger is left click
            self.menu.popup(QCursor.pos())

    def handle_clipboard_change(self):
        """Handle clipboard changes with rate limiting"""
        current_time = time.time()
        if current_time - self._last_clipboard_check < 0.1:  # Limit to max 10 checks per second
            return
        self._last_clipboard_check = current_time
        
        if self._suppress_clipboard_monitoring:
            return
            
        if not self.auto_send_enabled:
            print("Auto-send is disabled, ignoring clipboard change")
            return
            
        new_text = self.clipboard.text()
        if new_text and new_text != self.last_clipboard_text:
            print(f"Clipboard changed, new text length: {len(new_text)}")
            # Store the new text before sending to prevent loops
            self.last_clipboard_text = new_text
            
            # Check if this text was just received (to prevent loops)
            if hasattr(self, '_last_received_text') and new_text == self._last_received_text:
                print("Ignoring clipboard change from received text")
                return
                
            if self.paired_devices:
                print(f"Found {len(self.paired_devices)} paired devices to send to")
                # Temporarily suppress clipboard monitoring while sending
                self._suppress_clipboard_monitoring = True
                try:
                    # Send to all connected devices
                    for device_id, (ip, interface_ip) in self.paired_devices.items():
                        print(f"Checking device {device_id} with IP {ip}")
                        if is_valid_interface(ip) and is_valid_interface(interface_ip):
                            print(f"Sending to device {device_id} at {ip}")
                            self.send_text_to_device(device_id, ip, new_text)
                        else:
                            print(f"Skipping device {device_id} due to invalid interface")
                finally:
                    self._suppress_clipboard_monitoring = False
            else:
                print("No paired devices found to send to")

    def send_text_to_device(self, device_id, ip, text):
        try:
            print(f"Creating socket to send text to {device_id} at {ip}")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if hasattr(self, 'listener'):
                local_interface = self.listener.interface_ip
                if not is_valid_interface(local_interface):
                    print(f"Warning: Local interface {local_interface} is not valid, attempting to find zerotier interface")
                    local_interface = get_local_ip()
                    if not is_valid_interface(local_interface):
                        print(f"Could not find valid zerotier interface")
                        return
                
                local_addr = (local_interface, 0)
                client.bind(local_addr)
                print(f"Bound client to local interface: {local_addr[0]}")
            
            client.settimeout(5)
            print(f"Connecting to {ip}:{self.listener.port}...")
            client.connect((ip, self.listener.port))
            print("Connected successfully")
            
            message = {
                'sender_id': self.device_id,
                'text': text
            }
            encoded_message = json.dumps(message).encode('utf-8')
            print(f"Sending message of size {len(encoded_message)} bytes")
            client.send(encoded_message)
            client.close()
            print(f"Successfully sent text to {device_id}")
        except Exception as e:
            print(f"Failed to send text to {device_id}: {str(e)}")

    def toggle_auto_send(self):
        self.auto_send_enabled = not self.auto_send_enabled
        print(f"Auto-send clipboard {'enabled' if self.auto_send_enabled else 'disabled'}")

    def toggle_auto_receive(self):
        self.auto_receive_enabled = not self.auto_receive_enabled
        print(f"Auto-copy received text {'enabled' if self.auto_receive_enabled else 'disabled'}")

    def setup_menu(self):
        # Create main menu
        main_menu = QMenu()
        
        # Device ID display (only in main menu)
        device_id_action = main_menu.addAction(f"Device ID: {self.device_id}")
        device_id_action.setEnabled(False)
        
        main_menu.addSeparator()
        
        # Connected Devices section
        if self.paired_devices:
            for device_id, (ip, interface_ip) in self.paired_devices.items():
                device_submenu = main_menu.addMenu(device_id)
                
                # Send text action for this device
                send_action = device_submenu.addAction("Send Text...")
                send_action.triggered.connect(
                    lambda checked=False, d=device_id: self.show_device_send_dialog(d)
                )
                
                # View history for this device
                history_action = device_submenu.addAction("View History")
                history_action.triggered.connect(
                    lambda checked=False, d=device_id: self.show_device_history(d)
                )
        
        main_menu.addSeparator()
        
        # Settings submenu
        settings_menu = main_menu.addMenu("Settings")
        
        # Auto-send toggle
        auto_send_action = settings_menu.addAction("Auto-send Clipboard")
        auto_send_action.setCheckable(True)
        auto_send_action.setChecked(self.auto_send_enabled)
        auto_send_action.triggered.connect(self.toggle_auto_send)
        
        # Auto-receive toggle
        auto_receive_action = settings_menu.addAction("Auto-copy Received Text")
        auto_receive_action.setCheckable(True)
        auto_receive_action.setChecked(self.auto_receive_enabled)
        auto_receive_action.triggered.connect(self.toggle_auto_receive)
        
        # View all history (in main menu)
        view_history_action = main_menu.addAction("View All History")
        view_history_action.triggered.connect(self.show_history_dialog)
        
        main_menu.addSeparator()
        
        # Quit action (in main menu)
        quit_action = main_menu.addAction("Quit Gweeb")
        quit_action.triggered.connect(self.quit_app)
        
        # Set as the tray's context menu
        self.menu = main_menu
        self.tray.setContextMenu(main_menu)

    def show_device_send_dialog(self, device_id):
        """Show send dialog for a specific device"""
        if device_id not in self.paired_devices:
            return
            
        # Close any existing dialog
        if self.current_dialog and self.current_dialog.isVisible():
            try:
                self.current_dialog.close()
            except:
                pass
        
        ip, interface_ip = self.paired_devices[device_id]
        if not is_valid_interface(ip) or not is_valid_interface(interface_ip):
            QMessageBox.warning(None, "Invalid Interface", 
                              "This device is not on the zerotier network (172.26.x.x)")
            return
        
        dialog = SendTextDialog(
            parent=self,
            target_id=device_id,
            port=self.listener.port,
            device_id=self.device_id,
            devices=self.paired_devices
        )
        self.current_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_device_history(self, device_id):
        """Show history for a specific device"""
        # Filter texts for this device
        device_texts = [text for text in self.received_texts if text.get('sender_id') == device_id]
        
        if not device_texts:
            QMessageBox.information(None, "No History", f"No messages received from {device_id}.")
            return
        
        # Close any existing dialog
        if hasattr(self, 'history_dialog') and self.history_dialog and self.history_dialog.isVisible():
            try:
                self.history_dialog.close()
            except:
                pass
        
        dialog = TextHistoryDialog(device_texts)
        self.history_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def handle_received_text(self, sender_id, text):
        if sender_id in self.paired_devices:
            print(f"Received text from {sender_id}, length: {len(text)}")
            # Store text with metadata
            text_entry = {
                'sender_id': sender_id,
                'text': text,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.received_texts.append(text_entry)
            
            # Only copy to clipboard if auto-receive is enabled
            if self.auto_receive_enabled:
                print(f"Auto-receive enabled, copying text to clipboard")
                # Store the text we're about to receive to prevent loops
                self._last_received_text = text
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                notification_text = f"Text copied from {sender_id}"
            else:
                print(f"Auto-receive disabled, text saved to history only")
                notification_text = f"Text received from {sender_id}"
            
            # Show notification
            try:
                if IS_LINUX and show_linux_notification("Gweeb", notification_text):
                    pass  # Linux notification shown successfully
                else:
                    # Fallback to Qt notifications
                    self.tray.showMessage(
                        "Gweeb",  # Title
                        notification_text,  # Message
                        QSystemTrayIcon.Information,  # Icon
                        2000  # Duration in ms (2 seconds)
                    )
            except Exception as e:
                print(f"Failed to show notification: {e}")
        else:
            print(f"Received text from unknown sender {sender_id}")

    def handle_device_found(self, device_id, ip_address, interface_ip):
        if device_id != self.device_id:  # Don't add ourselves
            if is_valid_interface(ip_address) and is_valid_interface(interface_ip):
                self.paired_devices[device_id] = (ip_address, interface_ip)
                print(f"Added device {device_id} at {ip_address} (interface: {interface_ip})")
                self.update_devices_menu()
            else:
                print(f"Ignoring device {device_id} due to invalid interface: {ip_address} / {interface_ip}")

    def handle_device_removed(self, device_id):
        if device_id in self.paired_devices:
            del self.paired_devices[device_id]
            self.update_devices_menu()

    def update_devices_menu(self):
        # Update the devices section in the menu
        self.setup_menu()
        self.tray.setContextMenu(self.menu)

    def show_history_dialog(self):
        if not self.received_texts:
            QMessageBox.information(None, "No History", "No messages received yet.")
            return
            
        # Close any existing dialog
        if hasattr(self, 'history_dialog') and self.history_dialog and self.history_dialog.isVisible():
            try:
                self.history_dialog.close()
            except:
                pass
        
        dialog = TextHistoryDialog(self.received_texts)
        self.history_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def force_quit(self):
        """Force quit the application and cleanup"""
        print("Force quitting Gweeb...")
        try:
            self.discovery.stop()
            self.listener.stop()
            self.listener.wait()
            self.tray.hide()
            self.app.quit()
        except:
            pass
        
        # Remove PID file
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
            
        # Kill our process and children
        force_kill_process(self.pid)

    def quit_app(self):
        """Normal quit with cleanup"""
        print("Shutting down Gweeb...")
        cleanup()

    def check_clipboard(self):
        """Periodically check clipboard contents"""
        if not self._suppress_clipboard_monitoring and self.auto_send_enabled:
            current_text = self.clipboard.text()
            if current_text and current_text != self.last_clipboard_text:
                self.handle_clipboard_change()

if __name__ == '__main__':
    # Add psutil to requirements if not present
    try:
        import psutil
    except ImportError:
        print("Installing required dependency: psutil")
        os.system(f"{sys.executable} -m pip install psutil")
        import psutil
    
    # Only try to install netifaces on non-Windows platforms
    if not IS_WINDOWS:
        try:
            import netifaces
        except ImportError:
            print("Installing required dependency: netifaces")
            os.system(f"{sys.executable} -m pip install netifaces")
            import netifaces
    
    # Install dbus-python on Linux if not present
    if IS_LINUX:
        try:
            import dbus
        except ImportError:
            print("Installing required dependency: dbus-python")
            os.system(f"{sys.executable} -m pip install dbus-python")
            try:
                import dbus
                HAVE_DBUS = True
            except ImportError:
                HAVE_DBUS = False
                print("Warning: Failed to install dbus-python, falling back to Qt notifications")
    
    # Check if another instance is running
    if IS_LINUX:
        pid_dir = os.path.expanduser("~/.local/share/gweeb")
        pid_file = os.path.join(pid_dir, 'gweeb.pid')
    else:
        pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gweeb.pid')
        
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                # Try to kill the old process if it exists
                force_kill_process(old_pid)
            except:
                pass
            os.remove(pid_file)
        except:
            pass
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    gweeb = Gweeb(app)
    sys.exit(app.exec())