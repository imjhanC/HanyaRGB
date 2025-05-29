import socket
import sys
import time
import argparse

class SimpleRGBControl:
    def __init__(self, ip='127.0.0.1', port=6742):
        self.ip = ip
        self.port = port
        self.socket = None
        
        # OpenRGB protocol constants
        self.HEADER_SIZE = 16
        self.PROTOCOL_VERSION = 1
        self.REQUEST_CONTROLLER_COUNT = 0
        self.REQUEST_CONTROLLER_DATA = 1
        self.SET_CLIENT_NAME = 50
        self.RGBCONTROLLER_UPDATELEDS = 1101
        
    def connect(self):
        """Connect to the OpenRGB server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            print(f"Connected to OpenRGB server at {self.ip}:{self.port}")
            
            # Set client name
            self._send_packet(self.SET_CLIENT_NAME, "Simple RGB Control".encode())
            
            return True
        except Exception as e:
            print(f"Failed to connect to OpenRGB server: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the OpenRGB server"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from OpenRGB server")
            
    def get_device_count(self):
        """Get the number of RGB devices"""
        try:
            self._send_packet(self.REQUEST_CONTROLLER_COUNT)
            data = self._read_packet()
            
            if data:
                count = int.from_bytes(data, byteorder='little')
                print(f"Found {count} RGB device(s)")
                return count
                
            return 0
        except Exception as e:
            print(f"Error getting device count: {e}")
            return 0
            
    def set_device_color(self, device_id, color):
        """Set all LEDs on a device to a specific color"""
        try:
            # Request device data to get LED count
            self._send_packet(self.REQUEST_CONTROLLER_DATA, device_id.to_bytes(4, byteorder='little'))
            device_data = self._read_packet()
            
            if not device_data:
                print(f"Error: Could not get data for device {device_id}")
                return False
                
            # Parse basic device info
            name_length = int.from_bytes(device_data[0:2], byteorder='little')
            device_name = device_data[2:2+name_length].decode()
            print(f"Setting color for device: {device_name}")
            
            # We need to find the LED count in the device data
            # This is a very simplified approach - the real structure is more complex
            offset = 2 + name_length  # Skip name
            
            # Skip a bunch of fields to get to the LED count
            # These offsets are approximate and might need adjustment
            offset += 50  # Skip to zones count (approximate)
            zones_count = int.from_bytes(device_data[offset:offset+2], byteorder='little')
            offset += 2 + (zones_count * 50)  # Skip zones data (approximate)
            
            # Get LED count
            leds_count = int.from_bytes(device_data[offset:offset+2], byteorder='little')
            print(f"Device has {leds_count} LEDs")
            
            # Prepare the update packet
            packet = bytearray()
            packet.extend(device_id.to_bytes(4, byteorder='little'))  # Device ID
            packet.extend(leds_count.to_bytes(2, byteorder='little'))  # LED count
            
            # Add color data for each LED
            for i in range(leds_count):
                packet.extend(bytes([color[0], color[1], color[2], 0xFF]))  # RGB + brightness
                
            # Send the update command
            self._send_packet(self.RGBCONTROLLER_UPDATELEDS, packet)
            print(f"Set color to RGB({color[0]}, {color[1]}, {color[2]})")
            
            return True
            
        except Exception as e:
            print(f"Error setting color: {e}")
            return False
            
    def _send_packet(self, command_id, data=b''):
        """Send a packet to the OpenRGB server"""
        try:
            # Create packet header
            header = bytearray()
            header.extend(len(data).to_bytes(4, byteorder='little'))  # Data length
            header.extend(self.PROTOCOL_VERSION.to_bytes(4, byteorder='little'))  # Protocol version
            header.extend(command_id.to_bytes(4, byteorder='little'))  # Command ID
            header.extend(bytes([0, 0, 0, 0]))  # Reserved
            
            # Send header followed by data
            self.socket.send(header + data)
            return True
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False
            
    def _read_packet(self):
        """Read a packet from the OpenRGB server"""
        try:
            # Read header
            header = self.socket.recv(self.HEADER_SIZE)
            if len(header) != self.HEADER_SIZE:
                print(f"Error: Received invalid header size ({len(header)} bytes)")
                return None
                
            # Parse data length from header
            data_len = int.from_bytes(header[0:4], byteorder='little')
            print(f"Expecting {data_len} bytes of data")
            
            # Read data
            data = b''
            bytes_read = 0
            
            while bytes_read < data_len:
                chunk = self.socket.recv(min(4096, data_len - bytes_read))
                if not chunk:
                    break
                    
                data += chunk
                bytes_read += len(chunk)
                
            print(f"Read {bytes_read} bytes of data")
            return data
            
        except Exception as e:
            print(f"Error reading packet: {e}")
            return None

def main():
    # Color presets
    color_presets = {
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
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simple RGB Control Script")
    parser.add_argument("--color", default="white", help="Color (red, green, blue, white, purple, cyan, yellow, orange, off)")
    parser.add_argument("--device", type=int, default=0, help="Device ID")
    args = parser.parse_args()
    
    # Get color
    if args.color in color_presets:
        color = color_presets[args.color]
    else:
        print(f"Unknown color: {args.color}")
        print("Available colors: " + ", ".join(color_presets.keys()))
        return
        
    # Connect to OpenRGB
    rgb_control = SimpleRGBControl()
    
    if not rgb_control.connect():
        print("Failed to connect to OpenRGB server")
        return
        
    try:
        # Get device count
        device_count = rgb_control.get_device_count()
        
        if device_count == 0:
            print("No RGB devices found")
            return
            
        # Check device ID
        if args.device >= device_count:
            print(f"Invalid device ID: {args.device}")
            print(f"Device ID must be between 0 and {device_count - 1}")
            return
            
        # Set color
        rgb_control.set_device_color(args.device, color)
        
    finally:
        # Disconnect
        rgb_control.disconnect()

if __name__ == "__main__":
    main()