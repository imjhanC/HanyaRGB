import socket
import sys
import time

def main():
    print("OpenRGB Debug Script")
    print("====================")
    
    # Connection settings
    ip = '127.0.0.1'
    port = 6742
    
    # OpenRGB protocol constants
    HEADER_SIZE = 16
    PROTOCOL_VERSION = 1
    REQUEST_CONTROLLER_COUNT = 0
    SET_CLIENT_NAME = 50
    
    try:
        # Create and connect socket
        print(f"Attempting to connect to {ip}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        print(f"Connected to OpenRGB server at {ip}:{port}")
        
        # Set client name
        print("Setting client name...")
        client_name = "RGB Debug Client"
        
        # Create header for SET_CLIENT_NAME command
        header = bytearray()
        header.extend(len(client_name).to_bytes(4, byteorder='little'))  # Data length
        header.extend(PROTOCOL_VERSION.to_bytes(4, byteorder='little'))  # Protocol version
        header.extend(SET_CLIENT_NAME.to_bytes(4, byteorder='little'))  # Command ID
        header.extend(bytes([0, 0, 0, 0]))  # Reserved
        
        # Send header followed by client name
        sock.send(header + client_name.encode())
        print("Client name set successfully")
        
        # Request controller count
        print("Requesting controller count...")
        
        # Create header for REQUEST_CONTROLLER_COUNT command
        header = bytearray()
        header.extend((0).to_bytes(4, byteorder='little'))  # Data length (0 for this command)
        header.extend(PROTOCOL_VERSION.to_bytes(4, byteorder='little'))  # Protocol version
        header.extend(REQUEST_CONTROLLER_COUNT.to_bytes(4, byteorder='little'))  # Command ID
        header.extend(bytes([0, 0, 0, 0]))  # Reserved
        
        # Send header
        sock.send(header)
        
        # Read response header
        print("Reading header response...")
        response_header = sock.recv(HEADER_SIZE)
        if len(response_header) != HEADER_SIZE:
            print(f"Error: Received invalid header size ({len(response_header)} bytes)")
            return
            
        # Parse data length from header
        data_len = int.from_bytes(response_header[0:4], byteorder='little')
        print(f"Response data length: {data_len} bytes")
        
        # Read data
        print("Reading response data...")
        data = sock.recv(data_len)
        
        if len(data) != data_len:
            print(f"Error: Received {len(data)} bytes, expected {data_len} bytes")
            return
            
        # Parse controller count
        controller_count = int.from_bytes(data, byteorder='little')
        print(f"Found {controller_count} RGB controllers")
        
        # Show controller details
        if controller_count > 0:
            print("\nFound RGB controllers! Your OpenRGB connection is working.")
        else:
            print("\nNo RGB controllers found. Make sure your devices are properly connected.")
        
    except ConnectionRefusedError:
        print("\nError: Connection refused!")
        print("Make sure OpenRGB is running and the SDK server is enabled:")
        print("1. Open OpenRGB")
        print("2. Go to Settings tab")
        print("3. Check 'Enable SDK Server'")
        print("4. Click 'Start Server'")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure OpenRGB is running")
        print("2. Check OpenRGB SDK server settings")
        print("3. Try restarting OpenRGB")
        print("4. Make sure no other program is using port 6742")
        
    finally:
        if 'sock' in locals() and sock:
            sock.close()
            print("Socket closed")

if __name__ == "__main__":
    main()