import customtkinter as ctk
from tkinter import messagebox
from openrgb.utils import RGBColor
import tkinter.colorchooser as colorchooser
# Set global appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ColorControlWindow(ctk.CTkToplevel):
    def __init__(self, parent, client, device):
        super().__init__(parent)
        
        # Store references
        self.parent = parent
        self.client = client
        self.device = device
        self.selected_zone = None
        self.zone_buttons = {}  # Store zone buttons for highlighting
        self.zone_colors = {}   # Store zone colors
        
        # Window setup
        self.title(f"Color Control - {device.name}")
        
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
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self.create_ui()
        
        # Bind resize event
        self.bind("<Configure>", self.on_window_resize)
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Color Control for {self.device.name}",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(pady=(10, 20))
        
        # Zone selection frame
        self.zone_frame = ctk.CTkFrame(self.main_frame)
        self.zone_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.zone_label = ctk.CTkLabel(
            self.zone_frame,
            text="Select Zone:",
            font=("Arial", 16, "bold")
        )
        self.zone_label.pack(pady=(10, 5))
        
        # Zone buttons container with scrollable frame
        self.zone_scroll_frame = ctk.CTkScrollableFrame(self.zone_frame)
        self.zone_scroll_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Load zones
        self.load_zones()
        
        # Color control section
        self.color_frame = ctk.CTkFrame(self.main_frame)
        self.color_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.color_label = ctk.CTkLabel(
            self.color_frame,
            text="Color Picker",
            font=("Arial", 16, "bold")
        )
        self.color_label.pack(pady=(10, 5))
        
        # Color picker button
        self.color_picker_btn = ctk.CTkButton(
            self.color_frame,
            text="Pick Color",
            command=self.pick_color,
            width=200,
            height=40
        )
        self.color_picker_btn.pack(pady=10)
        
        # RGB sliders frame
        self.sliders_frame = ctk.CTkFrame(self.color_frame)
        self.sliders_frame.pack(fill="x", padx=20, pady=10)
        
        # Red slider
        self.red_frame = ctk.CTkFrame(self.sliders_frame)
        self.red_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.red_label = ctk.CTkLabel(self.red_frame, text="Red:")
        self.red_label.pack(side="left", padx=(0, 10))
        
        self.red_value_label = ctk.CTkLabel(self.red_frame, text="255")
        self.red_value_label.pack(side="right")
        
        self.red_slider = ctk.CTkSlider(
            self.sliders_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.update_red_value
        )
        self.red_slider.pack(fill="x", padx=20, pady=(0, 10))
        
        # Green slider
        self.green_frame = ctk.CTkFrame(self.sliders_frame)
        self.green_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.green_label = ctk.CTkLabel(self.green_frame, text="Green:")
        self.green_label.pack(side="left", padx=(0, 10))
        
        self.green_value_label = ctk.CTkLabel(self.green_frame, text="255")
        self.green_value_label.pack(side="right")
        
        self.green_slider = ctk.CTkSlider(
            self.sliders_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.update_green_value
        )
        self.green_slider.pack(fill="x", padx=20, pady=(0, 10))
        
        # Blue slider
        self.blue_frame = ctk.CTkFrame(self.sliders_frame)
        self.blue_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.blue_label = ctk.CTkLabel(self.blue_frame, text="Blue:")
        self.blue_label.pack(side="left", padx=(0, 10))
        
        self.blue_value_label = ctk.CTkLabel(self.blue_frame, text="255")
        self.blue_value_label.pack(side="right")
        
        self.blue_slider = ctk.CTkSlider(
            self.sliders_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.update_blue_value
        )
        self.blue_slider.pack(fill="x", padx=20, pady=(0, 10))
        
        # Color preview
        self.preview_frame = ctk.CTkFrame(self.color_frame, width=100, height=100)
        self.preview_frame.pack(pady=20)
        
        # Initialize sliders to white
        self.red_slider.set(255)
        self.green_slider.set(255)
        self.blue_slider.set(255)
        
        # Update preview
        self.update_color()
    
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            # Update button layouts
            self.update_button_layout()
    
    def update_button_layout(self):
        """Update button layout based on window size"""
        try:
            # Get current window width
            window_width = self.winfo_width()
            
            # Calculate optimal button width and columns
            min_button_width = 250
            max_button_width = 400
            button_padding = 10
            
            # Calculate how many columns can fit
            available_width = window_width - 100  # Account for padding
            cols = max(1, available_width // (min_button_width + button_padding))
            
            # Calculate button width
            button_width = min(max_button_width, 
                             (available_width - (cols * button_padding)) // cols)
            
            # Update zone buttons layout
            for i, (zone, btn) in enumerate(self.zone_buttons.items()):
                btn.configure(width=button_width)
                btn.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky="ew")
            
            # Configure column weights
            for col in range(cols):
                self.zone_scroll_frame.grid_columnconfigure(col, weight=1)
                
        except Exception as e:
            print(f"Error updating button layout: {e}")
    
    def load_zones(self):
        """Load and display zones for the selected device"""
        try:
            # Clear existing zone buttons
            for widget in self.zone_scroll_frame.winfo_children():
                widget.destroy()
            self.zone_buttons.clear()
            self.zone_colors.clear()  # Clear stored colors
            
            # Get zones
            zones = self.device.zones
            
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
                btn.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
                self.zone_buttons[zone] = btn
                
                # Get and store initial color for each zone
                try:
                    if zone.leds:
                        current_color = zone.leds[0].colors[0]
                        self.zone_colors[zone] = (current_color.red, current_color.green, current_color.blue)
                except Exception as e:
                    print(f"Error getting initial color for zone {zone.name}: {e}")
                    self.zone_colors[zone] = (255, 255, 255)  # Default to white
            
            print(f"Loaded {len(zones)} zones for device: {self.device.name}")
            
            # Update button layout
            self.after(100, self.update_button_layout)
            
        except Exception as e:
            print(f"Error loading zones: {e}")
            messagebox.showerror("Error", f"Failed to load zones: {str(e)}")
    
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
        self.title_label.configure(
            text=f"Color Control for {self.device.name} - {zone.name}"
        )
        
        # Highlight selected button
        if zone in self.zone_buttons:
            self.zone_buttons[zone].configure(
                fg_color="red",
                hover_color="darkred"
            )
        
        # Get or set zone color
        if zone in self.zone_colors:
            # Use stored color if available
            r, g, b = self.zone_colors[zone]
        else:
            try:
                # Get the first LED's color as reference (assuming all LEDs in zone have same color)
                if zone.leds:
                    current_color = zone.leds[0].colors[0]  # Get first color of first LED
                    r, g, b = current_color.red, current_color.green, current_color.blue
                else:
                    r, g, b = 255, 255, 255  # Default to white if no LEDs
            except Exception as e:
                print(f"Error getting zone color: {e}")
                r, g, b = 255, 255, 255  # Default to white if error
        
        # Update sliders and value labels
        self.red_slider.set(r)
        self.green_slider.set(g)
        self.blue_slider.set(b)
        self.red_value_label.configure(text=str(r))
        self.green_value_label.configure(text=str(g))
        self.blue_value_label.configure(text=str(b))
        
        # Store the color if not already stored
        if zone not in self.zone_colors:
            self.zone_colors[zone] = (r, g, b)
        
        # Update preview
        self.update_color()
    
    def center_window(self):
        """Center the window on the screen"""
        # This method is no longer needed as we set the position in __init__
        pass
    
    def pick_color(self):
        """Open color picker dialog"""
        color = colorchooser.askcolor(title="Choose Color")[0]
        if color:
            r, g, b = color
            self.red_slider.set(r)
            self.green_slider.set(g)
            self.blue_slider.set(b)
            self.update_color()
    
    def update_color(self, *args):
        """Update the color based on slider values"""
        try:
            # Get RGB values from sliders
            r = int(self.red_slider.get())
            g = int(self.green_slider.get())
            b = int(self.blue_slider.get())
            
            # Update preview
            color_hex = f'#{r:02x}{g:02x}{b:02x}'
            self.preview_frame.configure(fg_color=color_hex)
            
            # Update device color
            if self.selected_zone:
                try:
                    # Create RGB color
                    color = RGBColor(r, g, b)
                    
                    # Apply color to selected zone
                    self.selected_zone.set_color(color)
                    
                    # Store the color for this zone
                    self.zone_colors[self.selected_zone] = (r, g, b)
                    
                except Exception as e:
                    print(f"Error updating color: {e}")
                    messagebox.showerror("Error", f"Failed to update color: {str(e)}")
            
        except Exception as e:
            print(f"Error in update_color: {e}")
    
    def update_red_value(self, value):
        """Update red value label"""
        self.red_value_label.configure(text=str(int(value)))
        self.update_color()
    
    def update_green_value(self, value):
        """Update green value label"""
        self.green_value_label.configure(text=str(int(value)))
        self.update_color()
    
    def update_blue_value(self, value):
        """Update blue value label"""
        self.blue_value_label.configure(text=str(int(value)))
        self.update_color()
    
    def on_closing(self):
        """Handle window closing"""
        self.grab_release()
        self.destroy()
