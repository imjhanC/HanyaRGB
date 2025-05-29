from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

# Connect to OpenRGB
client = OpenRGBClient()
client.connect()

# Find your motherboard
target_device = None
for device in client.devices:
    if device.name == "ASUS TUF GAMING B760M-PLUS WIFI":
        target_device = device
        break

if target_device:
    print(f"Found motherboard: {target_device.name}")
    print(f"Zones: {len(target_device.zones)} | LEDs: {len(target_device.leds)}")

    # Print zone details
    for i, zone in enumerate(target_device.zones):
        print(f"[Zone {i}] {zone.name} - {len(zone.leds)} LEDs")

    # Set each zone to a different color
    colors = [
        RGBColor(255, 0, 0),   # Red
        RGBColor(0, 255, 0),   # Green
        RGBColor(255, 0, 255),   # Blue
        RGBColor(255, 255, 255), # Yellow
    ]

    for i, zone in enumerate(target_device.zones):
        color = colors[i % len(colors)]
        print(f"Setting zone '{zone.name}' to {color}")
        zone.set_color(color)

else:
    print("Motherboard not found.")
