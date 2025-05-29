import tkinter as tk
from tkinter import colorchooser, Scale, HORIZONTAL
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
import threading
import math
import random

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
root.title(f"RGB LED Control - {target_zone.name} ({num_leds} LEDs)")
root.geometry("800x600")  # Larger window to fit more controls

# Frame for LED control buttons
led_frame = tk.Frame(root)
led_frame.pack(pady=10)

# Frame for special lighting effect buttons
effect_frame = tk.Frame(root)
effect_frame.pack(pady=10)

# Frame for effect control settings
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

# Dictionary to store button references for live updates
buttons = {}

# Global variables for effect control
running_effect = False
effect_speed = 50  # Default speed (0-100)

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

def reset_leds_to_black():
    """Reset all LEDs to black (off)"""
    for i in range(num_leds):
        target_zone.leds[i].set_color(RGBColor(0, 0, 0))  # Set to black (off)
        buttons[i].configure(bg="#000000")  # Update button color to black

def get_delay():
    """Calculate delay based on speed slider (inverse relationship)"""
    return 0.1 * (100 - effect_speed) / 100 + 0.01  # Range: 0.01s (fast) to 0.11s (slow)

def stop_current_effect():
    """Stop any currently running effects"""
    global running_effect
    running_effect = False
    time.sleep(0.2)  # Give the effect time to stop
    print("Stopping effect...")

def disable_led_buttons():
    """Disable all LED buttons while a special effect is running"""
    for i in range(num_leds):
        buttons[i].config(state=tk.DISABLED)

def enable_led_buttons():
    """Enable all LED buttons after the effect is complete"""
    for i in range(num_leds):
        buttons[i].config(state=tk.NORMAL)

# ================= LIGHTING EFFECTS =================

def apply_rainbow_effect():
    """Apply a flowing rainbow effect across all LEDs continuously until stopped"""
    global running_effect
    running_effect = True
    print("Applying rainbow effect... Press 'Stop Effect' to end")
    
    frame = 0
    while running_effect:
        for i in range(num_leds):
            # Create a rainbow pattern that spans across all LEDs
            hue = (i / num_leds + frame / 100) % 1.0
            
            # Convert HSV to RGB
            if hue < 1/6:
                r, g, b = 255, int(255 * 6 * hue), 0
            elif hue < 2/6:
                r, g, b = int(255 * (2 - 6 * hue)), 255, 0
            elif hue < 3/6:
                r, g, b = 0, 255, int(255 * (6 * hue - 2))
            elif hue < 4/6:
                r, g, b = 0, int(255 * (4 - 6 * hue)), 255
            elif hue < 5/6:
                r, g, b = int(255 * (6 * hue - 4)), 0, 255
            else:
                r, g, b = 255, 0, int(255 * (6 - 6 * hue))
            
            # Set the color
            color = RGBColor(r, g, b)
            target_zone.leds[i].set_color(color)
        
        # Delay between frames for smooth animation
        time.sleep(get_delay())
        
        # Increment frame counter for animation
        frame = (frame + 1) % 100
    
    print("Rainbow effect stopped.")
    enable_led_buttons()

def apply_color_wave_effect():
    """Apply a wave of a single color moving across the LEDs"""
    global running_effect
    running_effect = True
    print("Applying color wave effect... Press 'Stop Effect' to end")
    
    # Choose a color for the wave
    colors = [
        RGBColor(255, 0, 0),    # Red
        RGBColor(0, 255, 0),    # Green
        RGBColor(0, 0, 255),    # Blue
        RGBColor(255, 255, 0),  # Yellow
        RGBColor(255, 0, 255),  # Purple
        RGBColor(0, 255, 255),  # Cyan
    ]
    
    wave_position = 0
    color_index = 0
    
    while running_effect:
        for i in range(num_leds):
            # Calculate brightness based on position in wave
            distance = (i - wave_position) % num_leds
            brightness = 1.0 - min(distance, num_leds - distance) / (num_leds / 3)
            brightness = max(0, brightness)
            
            # Apply brightness to base color
            color = colors[color_index]
            r = int(color.red * brightness)
            g = int(color.green * brightness)
            b = int(color.blue * brightness)
            
            target_zone.leds[i].set_color(RGBColor(r, g, b))
        
        # Move wave position
        wave_position = (wave_position + 1) % num_leds
        
        # Change color every full cycle
        if wave_position == 0:
            color_index = (color_index + 1) % len(colors)
        
        time.sleep(get_delay())
    
    print("Color wave effect stopped.")
    enable_led_buttons()

def apply_breathing_effect():
    """Apply a breathing effect - fading in and out"""
    global running_effect
    running_effect = True
    print("Applying breathing effect... Press 'Stop Effect' to end")
    
    # Choose a series of colors to breathe through
    colors = [
        RGBColor(255, 0, 0),    # Red
        RGBColor(0, 255, 0),    # Green
        RGBColor(0, 0, 255),    # Blue
        RGBColor(255, 255, 0),  # Yellow
        RGBColor(255, 0, 255),  # Purple
        RGBColor(0, 255, 255),  # Cyan
    ]
    color_index = 0
    
    while running_effect:
        # Calculate 100 steps of brightness for smooth breathing
        for step in range(200):
            # Use sine wave for smooth breathing effect (0 to 1 to 0)
            if step < 100:
                brightness = math.sin(step * math.pi / 100)
            else:
                brightness = 0  # Brief off period between colors
            
            color = colors[color_index]
            r = int(color.red * brightness)
            g = int(color.green * brightness)
            b = int(color.blue * brightness)
            
            # Apply to all LEDs
            for i in range(num_leds):
                target_zone.leds[i].set_color(RGBColor(r, g, b))
            
            time.sleep(get_delay() / 2)  # Faster breathing
            
            # Change color when breathing cycle completes
            if step == 199:
                color_index = (color_index + 1) % len(colors)
    
    print("Breathing effect stopped.")
    enable_led_buttons()

def apply_fire_effect():
    """Apply a flickering fire effect across all LEDs"""
    global running_effect
    running_effect = True
    print("Applying fire effect... Press 'Stop Effect' to end")
    
    while running_effect:
        for i in range(num_leds):
            # Fire effect uses oranges and reds with random intensity
            red = random.randint(200, 255)
            green = random.randint(50, 150)
            blue = random.randint(0, 20)
            
            # LEDs closer to center are brighter (like the base of a flame)
            center_distance = abs(i - num_leds // 2) / (num_leds // 2)
            intensity = 1.0 - 0.5 * center_distance
            
            # Add some flicker
            flicker = random.uniform(0.7, 1.0)
            intensity *= flicker
            
            r = int(red * intensity)
            g = int(green * intensity)
            b = int(blue * intensity)
            
            target_zone.leds[i].set_color(RGBColor(r, g, b))
        
        time.sleep(get_delay() * 1.5)  # Slower for realistic fire
    
    print("Fire effect stopped.")
    enable_led_buttons()

def apply_police_effect():
    """Apply a police light effect (red and blue flashing)"""
    global running_effect
    running_effect = True
    print("Applying police light effect... Press 'Stop Effect' to end")
    
    while running_effect:
        # Red phase
        for i in range(num_leds):
            if i < num_leds // 2:
                target_zone.leds[i].set_color(RGBColor(255, 0, 0))  # Red
            else:
                target_zone.leds[i].set_color(RGBColor(0, 0, 0))    # Off
        time.sleep(get_delay() * 3)
        
        # All off
        for i in range(num_leds):
            target_zone.leds[i].set_color(RGBColor(0, 0, 0))
        time.sleep(get_delay() * 0.5)
        
        # Blue phase
        for i in range(num_leds):
            if i >= num_leds // 2:
                target_zone.leds[i].set_color(RGBColor(0, 0, 255))  # Blue
            else:
                target_zone.leds[i].set_color(RGBColor(0, 0, 0))    # Off
        time.sleep(get_delay() * 3)
        
        # All off
        for i in range(num_leds):
            target_zone.leds[i].set_color(RGBColor(0, 0, 0))
        time.sleep(get_delay() * 0.5)
    
    print("Police effect stopped.")
    enable_led_buttons()

def apply_strobe_effect():
    """Apply a quick strobe flash effect"""
    global running_effect
    running_effect = True
    print("Applying strobe effect... Press 'Stop Effect' to end")
    
    # Colors to cycle through
    colors = [
        RGBColor(255, 255, 255),  # White
        RGBColor(255, 0, 0),      # Red
        RGBColor(0, 255, 0),      # Green
        RGBColor(0, 0, 255),      # Blue
    ]
    color_index = 0
    
    while running_effect:
        # Quick flash
        for i in range(num_leds):
            target_zone.leds[i].set_color(colors[color_index])
        time.sleep(get_delay() * 0.5)
        
        # Off
        for i in range(num_leds):
            target_zone.leds[i].set_color(RGBColor(0, 0, 0))
        time.sleep(get_delay() * 1.5)
        
        # Change color every 4 flashes
        if random.randint(0, 3) == 0:
            color_index = (color_index + 1) % len(colors)
    
    print("Strobe effect stopped.")
    enable_led_buttons()

def apply_meteor_effect():
    """Apply a meteor rain effect"""
    global running_effect
    running_effect = True
    print("Applying meteor effect... Press 'Stop Effect' to end")
    
    # Meteor parameters
    meteor_size = 3
    meteor_trail = 5
    meteor_color = RGBColor(255, 255, 255)  # White meteor
    
    while running_effect:
        # Clear all LEDs
        for i in range(num_leds):
            target_zone.leds[i].set_color(RGBColor(0, 0, 0))
        
        # Move meteor from right to left
        for i in range(num_leds + meteor_size + meteor_trail):
            # Fade out existing LEDs (simulating trail fading)
            for j in range(num_leds):
                current_color = target_zone.leds[j].colors[0]
                if current_color.red > 0 or current_color.green > 0 or current_color.blue > 0:
                    # Fade by ~20%
                    r = max(0, int(current_color.red * 0.8))
                    g = max(0, int(current_color.green * 0.8))
                    b = max(0, int(current_color.blue * 0.8))
                    target_zone.leds[j].set_color(RGBColor(r, g, b))
            
            # Draw meteor
            for j in range(meteor_size):
                if 0 <= i - j < num_leds:
                    target_zone.leds[i - j].set_color(meteor_color)
            
            time.sleep(get_delay())
            
            # Change meteor color every cycle
            if i == num_leds + meteor_size + meteor_trail - 1:
                # Generate a new random bright color
                h = random.random()  # Random hue
                # Convert HSV to RGB (bright, saturated color)
                if h < 1/6:
                    r, g, b = 255, int(255 * 6 * h), 0
                elif h < 2/6:
                    r, g, b = int(255 * (2 - 6 * h)), 255, 0
                elif h < 3/6:
                    r, g, b = 0, 255, int(255 * (6 * h - 2))
                elif h < 4/6:
                    r, g, b = 0, int(255 * (4 - 6 * h)), 255
                elif h < 5/6:
                    r, g, b = int(255 * (6 * h - 4)), 0, 255
                else:
                    r, g, b = 255, 0, int(255 * (6 - 6 * h))
                    
                meteor_color = RGBColor(r, g, b)
    
    print("Meteor effect stopped.")
    enable_led_buttons()

def apply_music_visualizer_effect():
    """Apply a simulated music visualizer effect"""
    global running_effect
    running_effect = True
    print("Applying music visualizer effect... Press 'Stop Effect' to end")
    
    frame = 0
    while running_effect:
        # For each LED, set a "volume" level based on sine waves
        for i in range(num_leds):
            # Use multiple sine waves to simulate a complex audio pattern
            wave1 = math.sin((i / num_leds * 4 + frame / 10) * math.pi * 2) * 0.5 + 0.5
            wave2 = math.sin((i / num_leds * 2 + frame / 15) * math.pi * 2) * 0.3 + 0.7
            wave3 = math.sin((i / num_leds + frame / 5) * math.pi * 2) * 0.2 + 0.8
            
            # Combine waves and limit to 0-1 range
            intensity = min(1.0, max(0, (wave1 * wave2 * wave3) ** 2))
            
            # Volume level determines color (green to yellow to red)
            if intensity < 0.3:
                r, g, b = int(intensity * 255 * 3), 255, 0
            elif intensity < 0.7:
                r, g, b = 255, int(255 * (1 - (intensity - 0.3) * 2.5)), 0
            else:
                r, g, b = 255, 0, int((intensity - 0.7) * 255 * 3)
            
            target_zone.leds[i].set_color(RGBColor(r, g, b))
        
        time.sleep(get_delay() * 0.8)
        frame += 1
    
    print("Music visualizer effect stopped.")
    enable_led_buttons()

# ================= GUI SETUP =================

# Create buttons for 18 LEDs in the LED control panel
for i in range(num_leds):
    # Get current color of the LED
    current_color = target_zone.leds[i].colors[0]
    hex_color = rgbcolor_to_hex(current_color)

    # Create a button for each LED inside the LED control panel
    btn = tk.Button(led_frame, text=f"LED {i}", bg=hex_color, command=lambda i=i: change_led_color(i), width=8)
    row = i // 6
    col = i % 6
    btn.grid(row=row, column=col, padx=5, pady=5)

    buttons[i] = btn  # Store button reference for updating later

# Create a separator
separator = tk.Frame(effect_frame, height=2, bg="gray")
separator.pack(fill="x", pady=10)

# Label for effects section
effect_label = tk.Label(effect_frame, text="LIGHTING EFFECTS", font=("Arial", 12, "bold"))
effect_label.pack(pady=5)

# Create effect buttons in rows of 3
effects = [
    ("Rainbow Flow", lambda: threading.Thread(target=apply_rainbow_effect, daemon=True).start()),
    ("Color Wave", lambda: threading.Thread(target=apply_color_wave_effect, daemon=True).start()),
    ("Breathing", lambda: threading.Thread(target=apply_breathing_effect, daemon=True).start()),
    ("Fire Effect", lambda: threading.Thread(target=apply_fire_effect, daemon=True).start()),
    ("Police Lights", lambda: threading.Thread(target=apply_police_effect, daemon=True).start()),
    ("Strobe Flash", lambda: threading.Thread(target=apply_strobe_effect, daemon=True).start()),
    ("Meteor Rain", lambda: threading.Thread(target=apply_meteor_effect, daemon=True).start()),
    ("Music Visualizer", lambda: threading.Thread(target=apply_music_visualizer_effect, daemon=True).start()),
]

# Create frames for each row of buttons
row_frames = []
for i in range((len(effects) + 2) // 3):  # Need enough rows for effects + stop button
    row_frame = tk.Frame(effect_frame)
    row_frame.pack(pady=5)
    row_frames.append(row_frame)

# Add effect buttons to rows
for i, (effect_name, effect_func) in enumerate(effects):
    row = i // 3
    col = i % 3
    
    def start_effect(effect_func=effect_func):
        stop_current_effect()  # Stop any existing effect
        disable_led_buttons()  # Disable LED buttons
        effect_func()          # Start the new effect
    
    btn = tk.Button(row_frames[row], text=effect_name, command=start_effect, width=15)
    btn.grid(row=0, column=col, padx=5)

# Add stop button in the next available position
row = len(effects) // 3
col = len(effects) % 3
stop_button = tk.Button(row_frames[row], text="STOP EFFECT", command=stop_current_effect, 
                       width=15, bg="red", fg="white", font=("Arial", 10, "bold"))
stop_button.grid(row=0, column=col, padx=5)

# Reset button
reset_button = tk.Button(row_frames[-1], text="Turn All Off", command=reset_leds_to_black, width=15)
reset_button.grid(row=0, column=(col+1)%3, padx=5)

# Add speed control slider
speed_frame = tk.Frame(control_frame)
speed_frame.pack(pady=10)

speed_label = tk.Label(speed_frame, text="Effect Speed:")
speed_label.pack(side=tk.LEFT, padx=5)

def update_speed(val):
    global effect_speed
    effect_speed = int(val)

speed_slider = Scale(speed_frame, from_=1, to=100, orient=HORIZONTAL, 
                    command=update_speed, length=200)
speed_slider.set(effect_speed)
speed_slider.pack(side=tk.LEFT, padx=5)

root.mainloop()