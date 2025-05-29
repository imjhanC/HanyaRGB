import tkinter as tk
from tkinter import colorchooser
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

# Connect to OpenRGB
client = OpenRGBClient()
client.connect()

# Find the target device and zone
target_device = next((d for d in client.devices if d.name == "ASUS TUF GAMING B760M-PLUS WIFI"), None)

# Pick the zone you want to control (e.g., first ARGB header)
target_zone_name = "Addressable 1"
target_zone = next((z for z in target_device.zones if target_zone_name in z.name), None) if target_device else None

if not target_zone:
    print("Target zone not found.")
    exit()

# Limit number of LEDs to 18
num_leds = min(18, len(target_zone.leds))

# GUI App
root = tk.Tk()
root.title(f"Control LEDs - {target_zone.name} (18 LEDs)")

# Dictionary to store button references for live updates
buttons = {}

def rgbcolor_to_hex(color: RGBColor) -> str:
    """Convert RGBColor to hex format for Tkinter button color"""
    return f'#{color.red:02x}{color.green:02x}{color.blue:02x}'

def change_led_color(led_index):
    """Change the color of the selected LED"""
    color_code = colorchooser.askcolor(title=f"Choose color for LED {led_index}")
    if color_code[0]:
        r, g, b = map(int, color_code[0])
        color = RGBColor(r, g, b)
        print(f"LED {led_index} -> {color}")

        # Force static/manual mode
        target_zone.mode = 'direct'
        target_zone.leds[led_index].set_color(color)

        # Update button background to reflect the new color
        buttons[led_index].configure(bg=rgbcolor_to_hex(color))

# Create buttons for 18 LEDs
for i in range(num_leds):
    # Get current color of the LED
    current_color = target_zone.leds[i].colors[0]  # Accessing the first color (usually only one)
    hex_color = rgbcolor_to_hex(current_color)

    # Create a button for each LED
    btn = tk.Button(root, text=f"LED {i}", bg=hex_color, command=lambda i=i: change_led_color(i), width=10)
    btn.grid(row=i // 6, column=i % 6, padx=5, pady=5)

    buttons[i] = btn  # Store button reference for updating later

root.mainloop()
