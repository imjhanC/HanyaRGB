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
import tkinter.colorchooser as colorchooser
from threading import Thread
from color_control_window import ColorControlWindow
# Global variables
openrgb_server_process = None
client = None

# Set global appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# For connecting to OpenRGB server and application 
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
        
        # Bind resize event for responsive design
        self.bind("<Configure>", self.on_window_resize)
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=60)
        
        # Title section
        self.title_frame = ctk.CTkFrame(self.main_frame)
        self.title_frame.pack(fill="x", padx=20, pady=(20, 20))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame, 
            text="RGB Control Panel", 
            font=("Arial", 28, "bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        self.status_label = ctk.CTkLabel(
            self.title_frame, 
            text="Initializing OpenRGB...", 
            font=("Arial", 14)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Device selection section
        self.device_frame = ctk.CTkFrame(self.main_frame)
        self.device_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.device_label = ctk.CTkLabel(
            self.device_frame, 
            text="Select Device:", 
            font=("Arial", 16, "bold")
        )
        self.device_label.pack(pady=(10, 10))
        
        # Device buttons container with scrollable frame
        self.device_buttons_frame = ctk.CTkScrollableFrame(self.device_frame)
        self.device_buttons_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Bottom control section
        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.control_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.control_frame,
            text="Refresh Devices",
            command=self.refresh_devices,
            width=200,
            height=40
        )
        self.refresh_btn.pack(pady=10)
    
    def on_window_resize(self, event):
        """Handle window resize events to make buttons responsive"""
        # Only handle resize events for the main window
        if event.widget == self:
            self.update_button_layout()
    
    def update_button_layout(self):
        """Update button layout based on current window size"""
        try:
            # Get current window width
            window_width = self.winfo_width()
            
            # Calculate optimal button width and columns for device buttons
            min_button_width = 250
            max_button_width = 400
            button_padding = 10
            
            # Calculate how many columns can fit
            available_width = window_width - 100  # Account for padding
            cols = max(1, available_width // (min_button_width + button_padding))
            
            # Calculate button width
            button_width = min(max_button_width, 
                             (available_width - (cols * button_padding)) // cols)
            
            # Update device buttons layout
            for i, widget in enumerate(self.device_buttons_frame.winfo_children()):
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(width=button_width)
                    widget.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky="ew")
            
            # Configure column weights for device buttons frame
            for col in range(cols):
                self.device_buttons_frame.grid_columnconfigure(col, weight=1)
                
        except Exception as e:
            # Silently handle any resize errors to avoid spam
            pass
    
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
            
            self.status_label.configure(text="Connected! Select a device.")
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
                btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
            print(f"Loaded {len(devices)} devices")
            
            # Update button layout after loading
            self.after(100, self.update_button_layout)
            
        except Exception as e:
            print(f"Error loading devices: {e}")
            self.status_label.configure(text=f"Error loading devices: {str(e)}")
    
    def select_device(self, device):
        """Select a device and open color control window"""
        self.selected_device = device
        
        # Update status
        self.status_label.configure(text=f"Selected device: {device.name}")
        
        # Open color control window
        self.open_color_control_window()
    
    def open_color_control_window(self):
        """Open the color control window"""
        if not self.selected_device or not self.client:
            return
        
        try:
            from color_control_window import ColorControlWindow
            # Hide main window
            self.withdraw()
            color_window = ColorControlWindow(self, self.client, self.selected_device)
            # Show main window when color window is closed
            color_window.protocol("WM_DELETE_WINDOW", lambda: self.on_color_window_close(color_window))
        except Exception as e:
            print(f"Error opening color control window: {e}")
            messagebox.showerror("Error", f"Failed to open color control window: {str(e)}")
            # Show main window if there's an error
            self.deiconify()
    
    def on_color_window_close(self, color_window):
        """Handle color window closing"""
        color_window.destroy()
        self.deiconify()  # Show main window again
    
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