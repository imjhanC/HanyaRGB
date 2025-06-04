import customtkinter as ctk
import tkinter as tk
from openrgb.utils import RGBColor
import threading
import time

class LEDControlWindow(ctk.CTkToplevel):
    def __init__(self, parent, client, device, zones, initial_led_counts=None):
        super().__init__(parent)
        
        self.parent = parent
        self.client = client
        self.device = device
        self.zones = zones
        self.zone_led_counts = {}  # Store LED counts for each zone
        self.update_thread = None
        self.updating = False
        
        # Initialize LED counts from initial_led_counts if provided, otherwise from zones
        if initial_led_counts:
            self.zone_led_counts = initial_led_counts.copy()
        else:
            for zone in zones:
                self.zone_led_counts[zone] = len(zone.leds)
        
        # Window setup
        self.title("LED Control")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # Center window on screen
        window_width = 800
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Make window stay on top initially
        self.lift()
        self.focus_force()
        
        # Create UI
        self.create_ui()
        
        # Set up protocol handler for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        """Create the LED control interface"""
        # Main container
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="LED Control",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Create zone controls
        for zone in self.zones:
            self.create_zone_control(zone)
        
        # Add Apply button at the bottom
        self.apply_btn = ctk.CTkButton(
            self.main_frame,
            text="Apply Changes",
            command=self.apply_changes,
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.apply_btn.pack(pady=20)
    
    def create_zone_control(self, zone):
        """Create controls for a single zone"""
        # Zone frame
        zone_frame = ctk.CTkFrame(self.main_frame)
        zone_frame.pack(fill="x", padx=10, pady=10)
        
        # Zone name and total LED count
        zone_label = ctk.CTkLabel(
            zone_frame,
            text=f"{zone.name} ({len(zone.leds)} LEDs)",
            font=("Arial", 16, "bold")
        )
        zone_label.pack(pady=(10, 5))
        
        # Control frame for buttons and count
        control_frame = ctk.CTkFrame(zone_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Decrease button
        decrease_btn = ctk.CTkButton(
            control_frame,
            text="-",
            width=40,
            command=lambda: self.adjust_led_count(zone, -1)
        )
        decrease_btn.pack(side="left", padx=5)
        
        # LED count entry
        count_entry = ctk.CTkEntry(
            control_frame,
            width=60,
            justify="center"
        )
        count_entry.insert(0, str(self.zone_led_counts[zone]))
        count_entry.bind("<KeyRelease>", lambda e: self.on_count_entry_change(zone, count_entry))
        count_entry.pack(side="left", padx=10)
        
        # Increase button
        increase_btn = ctk.CTkButton(
            control_frame,
            text="+",
            width=40,
            command=lambda: self.adjust_led_count(zone, 1)
        )
        increase_btn.pack(side="left", padx=5)
        
        # Preview frame for LED boxes
        preview_frame = ctk.CTkFrame(zone_frame)
        preview_frame.pack(fill="x", padx=10, pady=5)
        
        # Create LED preview boxes
        self.create_led_preview(preview_frame, zone)
        
        # Store references
        zone.control_frame = control_frame
        zone.count_entry = count_entry
        zone.preview_frame = preview_frame
    
    def on_count_entry_change(self, zone, entry):
        """Handle direct LED count input"""
        try:
            new_count = int(entry.get())
            if new_count >= 0:
                self.zone_led_counts[zone] = new_count
                self.create_led_preview(zone.preview_frame, zone)
                self.update_zone_leds(zone)
        except ValueError:
            # If invalid input, revert to previous value
            entry.delete(0, "end")
            entry.insert(0, str(self.zone_led_counts[zone]))
    
    def create_led_preview(self, preview_frame, zone):
        """Create LED preview boxes for a zone"""
        # Clear existing preview boxes
        for widget in preview_frame.winfo_children():
            widget.destroy()
        
        # Calculate number of boxes to show (max 24)
        num_boxes = min(24, self.zone_led_counts[zone])
        
        # Create boxes
        for i in range(num_boxes):
            # If we're showing more LEDs than the zone has, show them in a different color
            if i >= len(zone.leds):
                box = ctk.CTkFrame(
                    preview_frame,
                    width=20,
                    height=20,
                    fg_color="yellow"  # Use yellow to indicate exceeding original count
                )
            else:
                box = ctk.CTkFrame(
                    preview_frame,
                    width=20,
                    height=20,
                    fg_color="white" if i < self.zone_led_counts[zone] - 1 else "red"
                )
            box.pack(side="left", padx=2, pady=2)
    
    def adjust_led_count(self, zone, delta):
        """Adjust the number of LEDs for a zone"""
        current_count = self.zone_led_counts[zone]
        new_count = current_count + delta
        
        # Only check for minimum (0), allow exceeding maximum
        if new_count >= 0:
            self.zone_led_counts[zone] = new_count
            zone.count_entry.delete(0, "end")
            zone.count_entry.insert(0, str(new_count))
            self.create_led_preview(zone.preview_frame, zone)
            self.update_zone_leds(zone)
    
    def update_zone_leds(self, zone):
        """Update the actual LEDs in the zone"""
        if not self.client:
            return
        
        # Throttle updates to avoid overwhelming the RGB device
        if self.updating:
            return
        
        self.updating = True
        
        def update_leds():
            try:
                # Set all LEDs to white except the last one
                for i in range(len(zone.leds)):
                    if i < self.zone_led_counts[zone] - 1:
                        # White color
                        zone.leds[i].set_color(RGBColor(255, 255, 255))
                    elif i < self.zone_led_counts[zone]:
                        # Red color for the last active LED
                        zone.leds[i].set_color(RGBColor(255, 0, 0))
                    else:
                        # Turn off remaining LEDs
                        zone.leds[i].set_color(RGBColor(0, 0, 0))
                
                # Update the device
                self.client.update_device(self.device)
                
            except Exception as e:
                print(f"Error updating LEDs: {e}")
            finally:
                # Allow next update after short delay
                time.sleep(0.05)  # 50ms delay
                self.updating = False
        
        # Run LED update in separate thread to avoid blocking UI
        if self.update_thread is None or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=update_leds, daemon=True)
            self.update_thread.start()
    
    def apply_changes(self):
        """Apply changes and close window"""
        # Update parent window with new LED counts
        if hasattr(self.parent, 'update_zone_led_counts'):
            self.parent.update_zone_led_counts(self.zone_led_counts)
        # Release the grab before closing
        self.grab_release()
        self.destroy()
    
    def on_closing(self):
        """Handle window closing"""
        # Release the grab before closing
        self.grab_release()
        self.destroy()
