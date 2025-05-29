import socket
import json
import time
import sys
import argparse
from typing import List, Dict, Tuple, Optional

class OpenRGBClient:
    """Client for controlling RGB devices through OpenRGB"""
    
    # OpenRGB protocol constants
    HEADER_SIZE = 16
    PROTOCOL_VERSION = 1
    
    # Command types
    REQUEST_CONTROLLER_COUNT = 0
    REQUEST_CONTROLLER_DATA = 1
    REQUEST_PROTOCOL_VERSION = 40
    SET_CLIENT_NAME = 50
    RGBCONTROLLER_RESIZEZONE = 1000
    RGBCONTROLLER_UPDATELEDS = 1101
    RGBCONTROLLER_UPDATEMODE = 1102
    
    def __init__(self, ip: str = '127.0.0.1', port: int = 6742, name: str = 'ASUS RGB Controller'):
        """Initialize the OpenRGB client"""
        self.ip = ip
        self.port = port
        self.name = name
        self.socket = None
        self.device_count = 0
        self.devices = []
        
    def connect(self) -> bool:
        """Connect to the OpenRGB server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            print(f"Connected to OpenRGB server at {self.ip}:{self.port}")
            
            # Set client name
            self._send_packet(self.SET_CLIENT_NAME, self.name.encode())
            
            # Get device count
            self._send_packet(self.REQUEST_CONTROLLER_COUNT)
            response = self._read_packet()
            if response:
                self.device_count = int.from_bytes(response, byteorder='little')
                print(f"Found {self.device_count} RGB device(s)")
                return True
            return False
        except Exception as e:
            print(f"Failed to connect to OpenRGB server: {e}")
            print("Make sure OpenRGB is running and the SDK server is enabled in OpenRGB settings!")
            return False
            
    def disconnect(self):
        """Disconnect from the OpenRGB server"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from OpenRGB server")
            
    def get_devices(self) -> List[Dict]:
        """Get a list of all available RGB devices"""
        self.devices = []
        
        for device_id in range(self.device_count):
            # Request device data
            self._send_packet(self.REQUEST_CONTROLLER_DATA, device_id.to_bytes(4, byteorder='little'))
            response = self._read_packet()
            
            if response:
                # Parse device data (simplified)
                device_name_length = int.from_bytes(response[0:2], byteorder='little')
                device_name = response[2:2+device_name_length].decode()
                
                # Store basic device info
                device = {
                    'id': device_id,
                    'name': device_name,
                    'type': self._get_device_type(device_name)
                }
                
                self.devices.append(device)
                print(f"Device {device_id}: {device_name}")
                
        return self.devices
        
    def set_color(self, device_id: int, color: Tuple[int, int, int]) -> bool:
        """Set all LEDs on a device to a specific color"""
        if not self.socket:
            print("Not connected to OpenRGB server")
            return False
            
        if device_id >= self.device_count:
            print(f"Invalid device ID: {device_id}")
            return False
            
        try:
            # Request device data to get LED count
            self._send_packet(self.REQUEST_CONTROLLER_DATA, device_id.to_bytes(4, byteorder='little'))
            response = self._read_packet()
            
            if not response:
                return False
                
            # This is a simplified approach - parse just enough to get LED count
            # Real implementation would parse the full device data structure
            device_name_length = int.from_bytes(response[0:2], byteorder='little')
            offset = 2 + device_name_length + 2  # Skip name, device type
            
            # Skip modes count and modes data (simplified)
            modes_count = int.from_bytes(response[offset:offset+2], byteorder='little')
            offset += 2
            
            # Skip mode data (simplified approach)
            offset += 50  # Approximate offset to reach zones count
            
            # Skip zones data (simplified)
            zones_count = int.from_bytes(response[offset:offset+2], byteorder='little')
            offset += 2 + (zones_count * 50)  # Skip zones (approximate)
            
            # Get LED count
            leds_count = int.from_bytes(response[offset:offset+2], byteorder='little')
            
            # Create packet to update all LEDs
            packet = bytearray()
            
            # Add device ID
            packet.extend(device_id.to_bytes(4, byteorder='little'))
            
            # Add LED count
            packet.extend(leds_count.to_bytes(2, byteorder='little'))
            
            # Add color data for each LED
            for i in range(leds_count):
                # Add red, green, blue values
                packet.extend(bytes([color[0], color[1], color[2], 0xFF]))  # RGB + brightness
                
            # Send update command
            self._send_packet(self.RGBCONTROLLER_UPDATELEDS, packet)
            
            print(f"Set device {device_id} color to RGB({color[0]}, {color[1]}, {color[2]})")
            return True
            
        except Exception as e:
            print(f"Error setting color: {e}")
            return False
            
    def _get_device_type(self, device_name: str) -> str:
        """Try to determine device type from name"""
        device_name_lower = device_name.lower()
        
        if "motherboard" in device_name_lower:
            return "motherboard"
        elif "ram" in device_name_lower or "memory" in device_name_lower:
            return "ram"
        elif "gpu" in device_name_lower or "graphics" in device_name_lower:
            return "gpu"
        elif "keyboard" in device_name_lower:
            return "keyboard"
        elif "mouse" in device_name_lower:
            return "mouse"
        elif "asus" in device_name_lower:
            return "asus"
        else:
            return "unknown"
    
    def _send_packet(self, command_id: int, data: bytes = b''):
        """Send a packet to the OpenRGB server"""
        if not self.socket:
            raise Exception("Not connected to OpenRGB server")
            
        # Create packet header
        header = bytearray()
        header.extend(len(data).to_bytes(4, byteorder='little'))  # Data length
        header.extend(self.PROTOCOL_VERSION.to_bytes(4, byteorder='little'))  # Protocol version
        header.extend(command_id.to_bytes(4, byteorder='little'))  # Command ID
        header.extend(bytes([0, 0, 0, 0]))  # Reserved
        
        # Send header followed by data
        self.socket.send(header + data)
        
    def _read_packet(self) -> Optional[bytes]:
        """Read a packet from the OpenRGB server"""
        if not self.socket:
            return None
            
        try:
            # Read header
            header = self.socket.recv(self.HEADER_SIZE)
            if len(header) != self.HEADER_SIZE:
                return None
                
            # Parse data length from header
            data_len = int.from_bytes(header[0:4], byteorder='little')
            
            # Read data
            data = b''
            bytes_remaining = data_len
            
            while bytes_remaining > 0:
                chunk = self.socket.recv(min(4096, bytes_remaining))
                if not chunk:
                    break
                    
                data += chunk
                bytes_remaining -= len(chunk)
                
            return data
            
        except Exception as e:
            print(f"Error reading packet: {e}")
            return None

# Color presets
COLOR_PRESETS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "purple": (128, 0, 128),
    "cyan": (0, 255, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "off": (0, 0, 0)
}

def parse_color(color_str: str) -> Tuple[int, int, int]:
    """Parse color string into RGB tuple"""
    # Check if it's a preset color
    if color_str.lower() in COLOR_PRESETS:
        return COLOR_PRESETS[color_str.lower()]
        
    # Check if it's an RGB value like "255,0,0"
    if "," in color_str:
        try:
            r, g, b = map(int, color_str.split(","))
            return (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            )
        except:
            pass
            
    # Default to white if color can't be parsed
    print(f"Invalid color '{color_str}', using white")
    return (255, 255, 255)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Control ASUS RGB lighting via OpenRGB")
    parser.add_argument("--ip", default="127.0.0.1", help="OpenRGB server IP address")
    parser.add_argument("--port", type=int, default=6742, help="OpenRGB server port")
    parser.add_argument("--list", action="store_true", help="List available RGB devices")
    parser.add_argument("--device", type=int, help="Device ID to control")
    parser.add_argument("--color", help="Color (name or R,G,B)")
    parser.add_argument("--cycle", action="store_true", help="Cycle through colors")
    args = parser.parse_args()
    
    # Create OpenRGB client
    client = OpenRGBClient(ip=args.ip, port=args.port)
    
    # Connect to server
    if not client.connect():
        print("Failed to connect to OpenRGB server")
        sys.exit(1)
        
    try:
        # Get list of devices
        devices = client.get_devices()
        
        if len(devices) == 0:
            print("No RGB devices found")
            sys.exit(1)
            
        # List devices if requested
        if args.list:
            print("\nAvailable RGB devices:")
            for device in devices:
                print(f"ID: {device['id']} | Name: {device['name']} | Type: {device['type']}")
            sys.exit(0)
            
        # Look for ASUS motherboard devices
        asus_devices = [d for d in devices if "asus" in d["name"].lower() or d["type"] == "motherboard" or d["type"] == "asus"]
        
        if not asus_devices:
            print("No ASUS devices found")
            sys.exit(1)
            
        # Select device to control
        target_device = None
        if args.device is not None:
            # Use specified device ID
            if args.device < len(devices):
                target_device = args.device
            else:
                print(f"Invalid device ID: {args.device}")
                sys.exit(1)
        else:
            # Use first ASUS device
            target_device = asus_devices[0]["id"]
            print(f"Using device: {devices[target_device]['name']} (ID: {target_device})")
            
        # Set color if specified
        if args.color:
            color = parse_color(args.color)
            client.set_color(target_device, color)
            
        # Cycle through colors if requested
        elif args.cycle:
            print("Cycling through colors (Ctrl+C to stop)...")
            colors = list(COLOR_PRESETS.values())
            try:
                while True:
                    for color in colors:
                        client.set_color(target_device, color)
                        time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopped color cycling")
                
        else:
            # Show available colors
            print("\nAvailable color presets:")
            for color_name in COLOR_PRESETS:
                rgb = COLOR_PRESETS[color_name]
                print(f"- {color_name}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
            print("\nUsage examples:")
            print(f"python {sys.argv[0]} --device {target_device} --color red")
            print(f"python {sys.argv[0]} --device {target_device} --color 255,0,0")
            print(f"python {sys.argv[0]} --device {target_device} --cycle")
            
    finally:
        # Disconnect from server
        client.disconnect()

if __name__ == "__main__":
    main()