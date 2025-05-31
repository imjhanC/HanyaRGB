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
        self.current_color = (255, 0, 0)  # Default red
        self.update_thread = None
        self.updating = False
        
        # Window setup
        self.title(f"Color Control - {device.name}")
        self.geometry("800x700")
        self.minsize(600, 500)
        
        # Make window stay on top initially
        self.lift()
        self.focus_force()
        
        # Create UI
        self.create_ui()
        
        # Load zones
        self.load_zones()
    
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
        
        # RGB sliders
        self.create_rgb_sliders()
        
        # RGB entry frame
        self.entry_frame = ctk.CTkFrame(self.color_frame)
        self.entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.create_rgb_entries()
        
        # Color picker button
        self.picker_btn = ctk.CTkButton(
            self.color_frame,
            text="Open System Color Picker",
            command=self.open_color_picker,
            width=200,
            height=40
        )
        self.picker_btn.pack(pady=20)
        
        # Quick colors frame
        self.quick_colors_frame = ctk.CTkFrame(self.color_frame)
        self.quick_colors_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.create_quick_colors()
    
    def create_rgb_sliders(self):
        """Create RGB sliders"""
        slider_frame = ctk.CTkFrame(self.sliders_frame)
        slider_frame.pack(fill="x", padx=10, pady=10)
        
        # Red slider
        self.red_label = ctk.CTkLabel(slider_frame, text="Red: 255", width=80)
        self.red_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.red_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_red_change
        )
        self.red_slider.set(255)
        self.red_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Green slider
        self.green_label = ctk.CTkLabel(slider_frame, text="Green: 0", width=80)
        self.green_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.green_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_green_change
        )
        self.green_slider.set(0)
        self.green_slider.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Blue slider
        self.blue_label = ctk.CTkLabel(slider_frame, text="Blue: 0", width=80)
        self.blue_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.blue_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_blue_change
        )
        self.blue_slider.set(0)
        self.blue_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Configure grid weights
        slider_frame.grid_columnconfigure(1, weight=1)
    
    def create_rgb_entries(self):
        """Create RGB entry boxes"""
        entry_container = ctk.CTkFrame(self.entry_frame)
        entry_container.pack(pady=10)
        
        # RGB entries
        ctk.CTkLabel(entry_container, text="RGB Values:", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 10)
        )
        
        ctk.CTkLabel(entry_container, text="R:").grid(row=1, column=0, padx=5)
        self.red_entry = ctk.CTkEntry(entry_container, width=60)
        self.red_entry.grid(row=1, column=1, padx=5)
        self.red_entry.insert(0, "255")
        self.red_entry.bind("<KeyRelease>", self.on_entry_change)
        
        ctk.CTkLabel(entry_container, text="G:").grid(row=1, column=2, padx=5)
        self.green_entry = ctk.CTkEntry(entry_container, width=60)
        self.green_entry.grid(row=1, column=3, padx=5)
        self.green_entry.insert(0, "0")
        self.green_entry.bind("<KeyRelease>", self.on_entry_change)
        
        ctk.CTkLabel(entry_container, text="B:").grid(row=1, column=4, padx=5)
        self.blue_entry = ctk.CTkEntry(entry_container, width=60)
        self.blue_entry.grid(row=1, column=5, padx=5)
        self.blue_entry.insert(0, "0")
        self.blue_entry.bind("<KeyRelease>", self.on_entry_change)
    
    def create_quick_colors(self):
        """Create quick color selection buttons"""
        ctk.CTkLabel(
            self.quick_colors_frame,
            text="Quick Colors:",
            font=("Arial", 14, "bold")
        ).pack(pady=(10, 5))
        
        colors_container = ctk.CTkFrame(self.quick_colors_frame)
        colors_container.pack(pady=(0, 10))
        
        # Quick color options
        quick_colors = [
            ("Red", (255, 0, 0)),
            ("Green", (0, 255, 0)),
            ("Blue", (0, 0, 255)),
            ("Yellow", (255, 255, 0)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255)),
            ("White", (255, 255, 255)),
            ("Off", (0, 0, 0))
        ]
        
        for i, (name, color) in enumerate(quick_colors):
            btn = ctk.CTkButton(
                colors_container,
                text=name,
                command=lambda c=color: self.set_color(c),
                width=80,
                height=30,
                fg_color=self.rgb_to_hex(color) if color != (0, 0, 0) else "#404040"
            )
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
    
    def load_zones(self):
        """Load zones as buttons"""
        try:
            # Clear existing zone buttons
            for widget in self.zone_buttons_frame.winfo_children():
                widget.destroy()
            
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
            
            # Configure grid weights
            for col in range(3):
                self.zone_buttons_frame.grid_columnconfigure(col, weight=1)
                
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    def select_zone(self, zone):
        """Select a zone for color control"""
        self.selected_zone = zone
        print(f"Selected zone: {zone.name}")
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def update_color_display(self):
        """Update the color preview and controls"""
        # Update preview
        self.color_preview.configure(fg_color=self.rgb_to_hex(self.current_color))
        
        # Update labels
        self.red_label.configure(text=f"Red: {int(self.current_color[0])}")
        self.green_label.configure(text=f"Green: {int(self.current_color[1])}")
        self.blue_label.configure(text=f"Blue: {int(self.current_color[2])}")
        
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
    
    def on_entry_change(self, event=None):
        """Handle RGB entry changes"""
        try:
            r = max(0, min(255, int(self.red_entry.get() or 0)))
            g = max(0, min(255, int(self.green_entry.get() or 0)))
            b = max(0, min(255, int(self.blue_entry.get() or 0)))
            
            self.current_color = (r, g, b)
            
            # Update sliders
            self.red_slider.set(r)
            self.green_slider.set(g)
            self.blue_slider.set(b)
            
            # Update display
            self.update_color_display()
            self.apply_color()
            
        except ValueError:
            pass  # Ignore invalid input
    
    def open_color_picker(self):
        """Open system color picker"""
        color = colorchooser.askcolor(
            color=self.rgb_to_hex(self.current_color),
            title="Choose Color"
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