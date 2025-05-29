import customtkinter as ctk
import os
import sys
import time
import atexit
import signal
import shutil
import psutil
import subprocess
from tkinter import messagebox
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

# Global variables
openrgb_server_process = None
client = None

# Set global appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def find_openrgb_executable():
    """Find OpenRGB executable in common locations"""
    possible_paths = [
        # Windows paths
        r"C:\Program Files\OpenRGB\OpenRGB.exe",
        r"C:\Program Files (x86)\OpenRGB\OpenRGB.exe",
        r".\OpenRGB.exe",
        r".\OpenRGB\OpenRGB.exe",
        # Linux paths
        "/usr/bin/openrgb",
        "/usr/local/bin/openrgb",
        "./openrgb",
        # macOS paths
        "/Applications/OpenRGB.app/Contents/MacOS/OpenRGB",
        "/usr/local/bin/openrgb",
    ]
    
    # Also check PATH
    path_executable = shutil.which("openrgb") or shutil.which("OpenRGB")
    if path_executable:
        possible_paths.insert(0, path_executable)
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def is_openrgb_server_running():
    """Check if OpenRGB server is already running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'openrgb' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('--server' in arg or '-s' in arg for arg in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def start_openrgb_server():
    """Start OpenRGB server if not already running"""
    global openrgb_server_process
    
    # Check if server is already running
    if is_openrgb_server_running():
        print("OpenRGB server is already running.")
        return True
    
    # Find OpenRGB executable
    openrgb_path = find_openrgb_executable()
    if not openrgb_path:
        messagebox.showerror(
            "OpenRGB Not Found", 
            "OpenRGB executable not found!\n\n"
            "Please install OpenRGB or place OpenRGB.exe in the same directory as this script.\n"
            "Download from: https://openrgb.org/"
        )
        return False
    
    try:
        # Start OpenRGB server
        print(f"Starting OpenRGB server from: {openrgb_path}")
        
        # Different startup commands for different platforms
        if sys.platform.startswith('win'):
            # Windows: Use CREATE_NO_WINDOW to hide console
            openrgb_server_process = subprocess.Popen(
                [openrgb_path, "--server", "--server-port", "6742"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Linux/macOS
            openrgb_server_process = subprocess.Popen(
                [openrgb_path, "--server", "--server-port", "6742"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if process is still running (didn't crash immediately)
        if openrgb_server_process.poll() is None:
            print("OpenRGB server started successfully!")
            return True
        else:
            print("OpenRGB server failed to start.")
            return False
            
    except FileNotFoundError:
        messagebox.showerror(
            "OpenRGB Error", 
            f"Could not start OpenRGB from: {openrgb_path}\n"
            "Please check if the file exists and is executable."
        )
        return False
    except Exception as e:
        messagebox.showerror(
            "OpenRGB Error", 
            f"Error starting OpenRGB server: {str(e)}"
        )
        return False

def stop_openrgb_server():
    """Stop the OpenRGB server process"""
    global openrgb_server_process
    
    if openrgb_server_process and openrgb_server_process.poll() is None:
        try:
            print("Stopping OpenRGB server...")
            openrgb_server_process.terminate()
            
            # Wait for graceful shutdown
            try:
                openrgb_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                openrgb_server_process.kill()
                openrgb_server_process.wait()
            
            print("OpenRGB server stopped.")
        except Exception as e:
            print(f"Error stopping OpenRGB server: {e}")

def cleanup_on_exit():
    """Cleanup function called when the application exits"""
    stop_openrgb_server()

def connect_to_openrgb():
    """Connect to OpenRGB with retry logic"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to OpenRGB (attempt {attempt + 1}/{max_retries})...")
            client = OpenRGBClient()
            client.connect()
            print("Successfully connected to OpenRGB!")
            return client
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                messagebox.showerror(
                    "Connection Error",
                    "Failed to connect to OpenRGB server after multiple attempts.\n\n"
                    "Please check:\n"
                    "1. OpenRGB is installed correctly\n"
                    "2. Your RGB hardware is detected\n"
                    "3. You have proper permissions\n"
                    "4. No firewall is blocking the connection"
                )
                return None

# Create main application window
class RGBControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Desired window size
        window_width = 1600
        window_height = 900

        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position x, y to center the window
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))

        # Set geometry with position
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(800, 600)
        self.title("RGB Control Panel")
        self.configure(bg_color="#1a1a1a")
        
        # Initialize variables
        self.selected_device = None
        self.selected_zone = None
        self.client = None
        
        # Create UI
        self.create_ui()
        
        # Initialize OpenRGB connection
        self.initialize_openrgb()
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="RGB Control Panel", 
            font=("Arial", 28, "bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame, 
            text="Initializing OpenRGB...", 
            font=("Arial", 14)
        )
        self.status_label.pack(pady=(0, 20))
        
        # Device selection frame
        self.device_frame = ctk.CTkFrame(self.main_frame)
        self.device_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.device_label = ctk.CTkLabel(
            self.device_frame, 
            text="Select Device:", 
            font=("Arial", 16, "bold")
        )
        self.device_label.pack(pady=(10, 5))
        
        # Device buttons container
        self.device_buttons_frame = ctk.CTkFrame(self.device_frame)
        self.device_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Zone selection frame
        self.zone_frame = ctk.CTkFrame(self.main_frame)
        self.zone_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.zone_label = ctk.CTkLabel(
            self.zone_frame, 
            text="Select Zone:", 
            font=("Arial", 16, "bold")
        )
        self.zone_label.pack(pady=(10, 5))
        
        # Zone buttons container with scrollable frame
        self.zone_scroll_frame = ctk.CTkScrollableFrame(self.zone_frame)
        self.zone_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Control frame
        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Color control buttons
        self.color_buttons_frame = ctk.CTkFrame(self.control_frame)
        self.color_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Add color control buttons
        colors = [
            ("Red", "#FF0000"),
            ("Green", "#00FF00"),
            ("Blue", "#0000FF"),
            ("Purple", "#FF00FF"),
            ("Yellow", "#FFFF00"),
            ("Cyan", "#00FFFF"),
            ("White", "#FFFFFF"),
            ("Off", "#000000")
        ]
        
        for i, (name, color) in enumerate(colors):
            btn = ctk.CTkButton(
                self.color_buttons_frame,
                text=name,
                fg_color=color,
                text_color="black" if color in ["#FFFF00", "#00FFFF", "#FFFFFF"] else "white",
                command=lambda c=color: self.set_zone_color(c),
                width=80,
                height=35
            )
            btn.grid(row=0, column=i, padx=5, pady=5)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.control_frame,
            text="Refresh Devices",
            command=self.refresh_devices,
            width=120,
            height=35
        )
        self.refresh_btn.pack(pady=10)
    
    def initialize_openrgb(self):
        """Initialize OpenRGB connection"""
        try:
            self.status_label.configure(text="Starting OpenRGB server...")
            self.update()
            
            # Start OpenRGB server
            if not start_openrgb_server():
                self.status_label.configure(text="Failed to start OpenRGB server")
                return
            
            self.status_label.configure(text="Connecting to OpenRGB...")
            self.update()
            
            # Connect to OpenRGB
            self.client = connect_to_openrgb()
            if not self.client:
                self.status_label.configure(text="Failed to connect to OpenRGB")
                return
            
            self.status_label.configure(text="Connected! Select a device and zone.")
            self.load_devices()
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            print(f"Initialization error: {e}")
    
    def load_devices(self):
        """Load and display available RGB devices"""
        if not self.client:
            return
        
        try:
            # Clear existing device buttons
            for widget in self.device_buttons_frame.winfo_children():
                widget.destroy()
            
            # Get devices
            devices = self.client.devices
            
            if not devices:
                no_device_label = ctk.CTkLabel(
                    self.device_buttons_frame, 
                    text="No RGB devices found"
                )
                no_device_label.pack(pady=10)
                return
            
            # Create device buttons
            for i, device in enumerate(devices):
                btn = ctk.CTkButton(
                    self.device_buttons_frame,
                    text=f"{device.name} ({len(device.zones)} zones)",
                    command=lambda d=device: self.select_device(d),
                    width=300,
                    height=40
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            
            print(f"Loaded {len(devices)} devices")
            
        except Exception as e:
            print(f"Error loading devices: {e}")
            self.status_label.configure(text=f"Error loading devices: {str(e)}")
    
    def select_device(self, device):
        """Select a device and load its zones"""
        self.selected_device = device
        self.selected_zone = None
        
        # Update status
        self.status_label.configure(text=f"Selected device: {device.name}")
        
        # Load zones for selected device
        self.load_zones()
    
    def load_zones(self):
        """Load and display zones for the selected device"""
        if not self.selected_device:
            return
        
        try:
            # Clear existing zone buttons
            for widget in self.zone_scroll_frame.winfo_children():
                widget.destroy()
            
            # Get zones
            zones = self.selected_device.zones
            
            if not zones:
                no_zone_label = ctk.CTkLabel(
                    self.zone_scroll_frame, 
                    text="No zones found for this device"
                )
                no_zone_label.pack(pady=10)
                return
            
            # Create zone buttons
            for i, zone in enumerate(zones):
                zone_info = f"{zone.name}\n({len(zone.leds)} LEDs)"
                btn = ctk.CTkButton(
                    self.zone_scroll_frame,
                    text=zone_info,
                    command=lambda z=zone: self.select_zone(z),
                    width=250,
                    height=60
                )
                btn.grid(row=i//4, column=i%4, padx=10, pady=10)
            
            print(f"Loaded {len(zones)} zones for device: {self.selected_device.name}")
            
        except Exception as e:
            print(f"Error loading zones: {e}")
            self.status_label.configure(text=f"Error loading zones: {str(e)}")
    
    def select_zone(self, zone):
        """Select a zone for control"""
        self.selected_zone = zone
        
        # Update status
        self.status_label.configure(
            text=f"Selected: {self.selected_device.name} -> {zone.name} ({len(zone.leds)} LEDs)"
        )
    
    def set_zone_color(self, hex_color):
        """Set the selected zone to a specific color"""
        if not self.selected_zone:
            messagebox.showwarning("No Zone Selected", "Please select a zone first!")
            return
        
        try:
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Create color
            color = RGBColor(r, g, b)
            
            # Set all LEDs in the zone to this color
            colors = [color] * len(self.selected_zone.leds)
            self.selected_zone.set_colors(colors)
            
            color_name = "Off" if hex_color == "000000" else f"RGB({r},{g},{b})"
            print(f"Set {self.selected_zone.name} to {color_name}")
            
        except Exception as e:
            print(f"Error setting zone color: {e}")
            messagebox.showerror("Error", f"Failed to set zone color: {str(e)}")
    
    def refresh_devices(self):
        """Refresh the device list"""
        if self.client:
            try:
                # Reconnect to get updated device list
                self.client.disconnect()
                time.sleep(1)
                self.client.connect()
                self.load_devices()
                self.status_label.configure(text="Devices refreshed!")
            except Exception as e:
                print(f"Error refreshing devices: {e}")
                self.status_label.configure(text=f"Error refreshing: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.client:
                self.client.disconnect()
            cleanup_on_exit()
        except:
            pass
        self.destroy()

# Register cleanup function
atexit.register(cleanup_on_exit)

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\nShutting down...")
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run the app
if __name__ == "__main__":
    print("Starting OpenRGB LED Controller...")
    
    app = RGBControlApp()
    
    # Set up proper cleanup on window close
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted")
    finally:
        cleanup_on_exit()