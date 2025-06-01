import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
import colorsys
import math
from openrgb.utils import RGBColor
import threading
import time

class ColorControlWindow(ctk.CTkToplevel):
    def __init__(self, parent, client, device):
        super().__init__(parent)
        
        self.parent = parent
        self.client = client
        self.device = device
        self.selected_zone = None
        self.update_thread = None
        self.updating = False
        self.zone_buttons = {}  # Store zone buttons for highlighting
        self.zone_colors = {}   # Store zone colors
        self.color_picker_window = None  # Store reference to color picker window
        
        # Get initial color from first zone if available
        try:
            if device.zones and device.zones[0].leds:
                initial_color = device.zones[0].leds[0].colors[0]
                self.current_color = (initial_color.red, initial_color.green, initial_color.blue)
            else:
                self.current_color = (255, 0, 0)  # Default red
        except Exception as e:
            print(f"Error getting initial color: {e}")
            self.current_color = (255, 0, 0)  # Default red
        
        # Window setup
        self.title(f"Color Control - {device.name}")
        self.geometry("800x700")
        self.minsize(800, 600)
        
        # Center window on screen
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
        
        # Make window stay on top initially
        self.lift()
        self.focus_force()
        
        # Create UI
        self.create_ui()
        
        # Load zones
        self.load_zones()
        
        # Select first zone if available
        if device.zones:
            self.select_zone(device.zones[0])
            
        # Set up protocol handler for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        """Create the color control interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Color Control - {self.device.name}",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=(10, 20))
        
        # Zone selection frame
        self.zone_frame = ctk.CTkFrame(self.main_frame)
        self.zone_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        self.zone_label = ctk.CTkLabel(
            self.zone_frame,
            text="Select Zone:",
            font=("Arial", 16, "bold")
        )
        self.zone_label.pack(pady=(10, 5))
        
        # Zone buttons container
        self.zone_buttons_frame = ctk.CTkScrollableFrame(self.zone_frame, height=120)
        self.zone_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Color control frame
        self.color_frame = ctk.CTkFrame(self.main_frame)
        self.color_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Color preview
        self.preview_frame = ctk.CTkFrame(self.color_frame)
        self.preview_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Current Color:",
            font=("Arial", 14, "bold")
        )
        self.preview_label.pack(pady=(10, 5))
        
        self.color_preview = ctk.CTkFrame(
            self.preview_frame,
            height=60,
            fg_color=self.rgb_to_hex(self.current_color)
        )
        self.color_preview.pack(fill="x", padx=20, pady=(0, 10))
        
        # RGB sliders frame
        self.sliders_frame = ctk.CTkFrame(self.color_frame)
        self.sliders_frame.pack(fill="x", padx=20, pady=10)
        
        # RGB sliders with entry fields
        self.create_rgb_sliders()
        
        # Color picker button
        self.picker_btn = ctk.CTkButton(
            self.color_frame,
            text="Open System Color Picker",
            command=self.open_color_picker,
            width=200,
            height=40
        )
        self.picker_btn.pack(pady=20)
        
        # LED buttons frame (for individual LED control)
        self.led_buttons_frame = ctk.CTkFrame(self.color_frame)
        self.led_buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    def create_rgb_sliders(self):
        """Create RGB sliders with entry fields"""
        slider_frame = ctk.CTkFrame(self.sliders_frame)
        slider_frame.pack(fill="x", padx=10, pady=10)
        
        # Red slider and entry
        self.red_label = ctk.CTkLabel(slider_frame, text="Red:", width=60)
        self.red_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.red_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_red_change
        )
        self.red_slider.set(self.current_color[0])
        self.red_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.red_entry = ctk.CTkEntry(slider_frame, width=50)
        self.red_entry.grid(row=0, column=2, padx=5, pady=5)
        self.red_entry.insert(0, str(int(self.current_color[0])))
        self.red_entry.bind("<KeyRelease>", self.on_red_entry_change)
        
        # Green slider and entry
        self.green_label = ctk.CTkLabel(slider_frame, text="Green:", width=60)
        self.green_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.green_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_green_change
        )
        self.green_slider.set(self.current_color[1])
        self.green_slider.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.green_entry = ctk.CTkEntry(slider_frame, width=50)
        self.green_entry.grid(row=1, column=2, padx=5, pady=5)
        self.green_entry.insert(0, str(int(self.current_color[1])))
        self.green_entry.bind("<KeyRelease>", self.on_green_entry_change)
        
        # Blue slider and entry
        self.blue_label = ctk.CTkLabel(slider_frame, text="Blue:", width=60)
        self.blue_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.blue_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_blue_change
        )
        self.blue_slider.set(self.current_color[2])
        self.blue_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.blue_entry = ctk.CTkEntry(slider_frame, width=50)
        self.blue_entry.grid(row=2, column=2, padx=5, pady=5)
        self.blue_entry.insert(0, str(int(self.current_color[2])))
        self.blue_entry.bind("<KeyRelease>", self.on_blue_entry_change)
        
        # Configure grid weights
        slider_frame.grid_columnconfigure(1, weight=1)
    
    def load_zones(self):
        """Load zones as buttons"""
        try:
            # Clear existing zone buttons
            for widget in self.zone_buttons_frame.winfo_children():
                widget.destroy()
            self.zone_buttons.clear()
            
            zones = self.device.zones
            
            if not zones:
                no_zone_label = ctk.CTkLabel(
                    self.zone_buttons_frame,
                    text="No zones found"
                )
                no_zone_label.pack(pady=10)
                return
            
            # Create zone buttons
            for i, zone in enumerate(zones):
                btn = ctk.CTkButton(
                    self.zone_buttons_frame,
                    text=f"{zone.name} ({len(zone.leds)} LEDs)",
                    command=lambda z=zone: self.select_zone(z),
                    width=200,
                    height=35
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
                self.zone_buttons[zone] = btn
                
                # Get and store initial color for each zone
                try:
                    if zone.leds:
                        current_color = zone.leds[0].colors[0]
                        self.zone_colors[zone] = (current_color.red, current_color.green, current_color.blue)
                except Exception as e:
                    print(f"Error getting initial color for zone {zone.name}: {e}")
                    self.zone_colors[zone] = (255, 255, 255)  # Default to white
            
            # Configure grid weights
            for col in range(3):
                self.zone_buttons_frame.grid_columnconfigure(col, weight=1)
                
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    def select_zone(self, zone):
        """Select a zone for color control"""
        # Reset previous selection
        if self.selected_zone and self.selected_zone in self.zone_buttons:
            self.zone_buttons[self.selected_zone].configure(
                fg_color=["#3B8ED0", "#1F6AA5"],  # Default color
                hover_color=["#36719F", "#144870"]  # Default hover color
            )
        
        # Update selection
        self.selected_zone = zone
        self.title(f"Color Control - {self.device.name} - {zone.name}")
        
        # Highlight selected button
        if zone in self.zone_buttons:
            self.zone_buttons[zone].configure(
                fg_color="red",
                hover_color="darkred"
            )
        
        # Get current color from the zone's LEDs
        try:
            if zone.leds:
                current_color = zone.leds[0].colors[0]  # Get first color of first LED
                self.current_color = (current_color.red, current_color.green, current_color.blue)
                # Update stored color
                self.zone_colors[zone] = self.current_color
            else:
                self.current_color = (255, 255, 255)  # Default to white if no LEDs
        except Exception as e:
            print(f"Error getting zone color: {e}")
            self.current_color = (255, 255, 255)  # Default to white if error
        
        # Update UI with the zone's color
        self.update_color_display()
        self.red_slider.set(self.current_color[0])
        self.green_slider.set(self.current_color[1])
        self.blue_slider.set(self.current_color[2])
        # Update LED buttons for this zone
        self.update_led_buttons()
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def update_color_display(self):
        """Update the color preview and controls"""
        # Update preview
        self.color_preview.configure(fg_color=self.rgb_to_hex(self.current_color))
        # Update entries
        self.red_entry.delete(0, "end")
        self.red_entry.insert(0, str(int(self.current_color[0])))
        self.green_entry.delete(0, "end")
        self.green_entry.insert(0, str(int(self.current_color[1])))
        self.blue_entry.delete(0, "end")
        self.blue_entry.insert(0, str(int(self.current_color[2])))
    
    def set_color(self, rgb):
        """Set the current color and update display"""
        self.current_color = rgb
        
        # Update sliders
        self.red_slider.set(rgb[0])
        self.green_slider.set(rgb[1])
        self.blue_slider.set(rgb[2])
        
        # Update display
        self.update_color_display()
        
        # Apply to selected zone
        self.apply_color()
    
    def on_red_change(self, value):
        """Handle red slider change"""
        self.current_color = (int(value), self.current_color[1], self.current_color[2])
        self.update_color_display()
        self.apply_color()
    
    def on_green_change(self, value):
        """Handle green slider change"""
        self.current_color = (self.current_color[0], int(value), self.current_color[2])
        self.update_color_display()
        self.apply_color()
    
    def on_blue_change(self, value):
        """Handle blue slider change"""
        self.current_color = (self.current_color[0], self.current_color[1], int(value))
        self.update_color_display()
        self.apply_color()
    
    def on_red_entry_change(self, event=None):
        value = self.get_entry_value(self.red_entry)
        self.red_slider.set(value)
        self.current_color = (value, self.current_color[1], self.current_color[2])
        self.update_color_display()
        self.apply_color()

    def on_green_entry_change(self, event=None):
        value = self.get_entry_value(self.green_entry)
        self.green_slider.set(value)
        self.current_color = (self.current_color[0], value, self.current_color[2])
        self.update_color_display()
        self.apply_color()

    def on_blue_entry_change(self, event=None):
        value = self.get_entry_value(self.blue_entry)
        self.blue_slider.set(value)
        self.current_color = (self.current_color[0], self.current_color[1], value)
        self.update_color_display()
        self.apply_color()

    def get_entry_value(self, entry):
        try:
            value = int(entry.get())
            return max(0, min(255, value))
        except ValueError:
            return 0
    
    def on_closing(self):
        """Handle window closing"""
        # Close color picker if it's open
        if self.color_picker_window:
            self.color_picker_window.destroy()
        # Destroy the main window
        self.destroy()
    
    def open_color_picker(self):
        """Open system color picker"""
        color = colorchooser.askcolor(
            color=self.rgb_to_hex(self.current_color),
            title="Choose Color",
            parent=self
        )
        
        if color[0]:  # If user didn't cancel
            rgb = tuple(int(c) for c in color[0])
            self.set_color(rgb)
    
    def apply_color(self):
        """Apply current color to selected zone"""
        if not self.selected_zone or not self.client:
            return
        
        # Throttle updates to avoid overwhelming the RGB device
        if self.updating:
            return
        
        self.updating = True
        
        def update_color():
            try:
                # Create RGBColor object
                rgb_color = RGBColor(
                    int(self.current_color[0]),
                    int(self.current_color[1]),
                    int(self.current_color[2])
                )
                
                # Apply color to all LEDs in the zone
                for i in range(len(self.selected_zone.leds)):
                    self.selected_zone.leds[i].set_color(rgb_color)
                
                # Update the device
                self.client.update_device(self.device)
                
                # Store the color for this zone
                self.zone_colors[self.selected_zone] = self.current_color
                
            except Exception as e:
                print(f"Error applying color: {e}")
            finally:
                # Allow next update after short delay
                time.sleep(0.05)  # 50ms delay
                self.updating = False
        
        # Run color update in separate thread to avoid blocking UI
        if self.update_thread is None or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=update_color, daemon=True)
            self.update_thread.start()

    def update_led_buttons(self):
        """Update the LED buttons for the selected zone"""
        # Clear previous buttons
        for widget in self.led_buttons_frame.winfo_children():
            widget.destroy()
        if not self.selected_zone or not hasattr(self.selected_zone, 'leds'):
            return
        leds = self.selected_zone.leds
        if not leds:
            return
        ctk.CTkLabel(self.led_buttons_frame, text="Individual LED Control:", font=("Arial", 14, "bold")).pack(pady=(0, 5))
        btns_frame = ctk.CTkFrame(self.led_buttons_frame)
        btns_frame.pack()
        for i, led in enumerate(leds):
            # Get current color of the LED
            try:
                color = led.colors[0]
                rgb = (color.red, color.green, color.blue)
            except Exception:
                rgb = (255, 255, 255)
            btn = ctk.CTkButton(
                btns_frame,
                width=40,
                height=40,
                fg_color=self.rgb_to_hex(rgb),
                text=str(i+1),
                command=lambda idx=i: self.pick_led_color(idx)
            )
            btn.grid(row=0, column=i, padx=3, pady=3)

    def pick_led_color(self, led_index):
        """Open color picker for a specific LED and set its color in real-time"""
        led = self.selected_zone.leds[led_index]
        try:
            color = led.colors[0]
            initial_rgb = (color.red, color.green, color.blue)
        except Exception:
            initial_rgb = (255, 255, 255)
        color = colorchooser.askcolor(
            color=self.rgb_to_hex(initial_rgb),
            title=f"Choose Color for LED {led_index+1}",
            parent=self
        )
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            from openrgb.utils import RGBColor
            rgb_color = RGBColor(*rgb)
            led.set_color(rgb_color)
            self.client.update_device(self.device)
            # Update button color
            self.update_led_buttons()