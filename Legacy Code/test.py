import sys
import os
import subprocess
import wmi

def check_device_manager():
    """Check if ASUS RGB controllers are visible in Device Manager"""
    print("Checking Device Manager for ASUS RGB controllers...")
    
    try:
        c = wmi.WMI()
        # Search for devices that might be related to ASUS RGB lighting
        devices = c.Win32_PnPEntity()
        
        asus_devices = []
        rgb_keywords = ["aura", "rgb", "led", "light", "asus"]
        
        for device in devices:
            if device.Name:
                name_lower = device.Name.lower()
                if "asus" in name_lower and any(keyword in name_lower for keyword in rgb_keywords):
                    asus_devices.append(device.Name)
                    
        if asus_devices:
            print("Found potential ASUS RGB devices:")
            for device in asus_devices:
                print(f"- {device}")
            return True
        else:
            print("No ASUS RGB devices found in Device Manager.")
            return False
            
    except Exception as e:
        print(f"Error checking Device Manager: {e}")
        return False

def check_aura_service():
    """Check if ASUS AURA service is running"""
    print("\nChecking for ASUS AURA Service...")
    
    try:
        c = wmi.WMI()
        services = c.Win32_Service(Name="LightingService")
        
        if len(services) > 0:
            service = services[0]
            print(f"AURA Service found: {service.Name}")
            print(f"Status: {service.State}")
            return True
        else:
            print("AURA Service not found.")
            
            # Check for alternative service names
            alt_services = ["AURA", "AsusROG", "LightingService"]
            for service_name in alt_services:
                services = c.Win32_Service(Name=service_name)
                if len(services) > 0:
                    service = services[0]
                    print(f"Alternative service found: {service.Name}")
                    print(f"Status: {service.State}")
                    return True
                    
            return False
            
    except Exception as e:
        print(f"Error checking AURA service: {e}")
        return False

def check_aura_sdk():
    """Check if AURA SDK is installed"""
    print("\nChecking for ASUS AURA SDK...")
    
    potential_paths = [
        r"C:\Program Files\ASUS\AURA SDK",
        r"C:\Program Files (x86)\ASUS\AURA SDK",
        r"C:\Program Files\ASUS\AURA"
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"AURA SDK found at: {path}")
            return True
            
    print("AURA SDK not found in common installation paths.")
    return False

def check_openrgb():
    """Check if OpenRGB can detect ASUS devices"""
    print("\nChecking for OpenRGB compatibility...")
    
    try:
        # Check if OpenRGB is installed
        openrgb_paths = [
            r"C:\Program Files\OpenRGB\OpenRGB.exe",
            r"C:\Program Files (x86)\OpenRGB\OpenRGB.exe"
        ]
        
        openrgb_path = None
        for path in openrgb_paths:
            if os.path.exists(path):
                openrgb_path = path
                break
                
        if openrgb_path:
            print(f"OpenRGB found at: {openrgb_path}")
            print("OpenRGB supports many ASUS motherboards and can be used as an alternative.")
            print("You can try running OpenRGB with the --list-devices flag to check compatibility.")
            return True
        else:
            print("OpenRGB not found. Consider installing it from: https://openrgb.org/")
            return False
            
    except Exception as e:
        print(f"Error checking OpenRGB: {e}")
        return False

def main():
    print("ASUS RGB Controller Detection Tool")
    print("==================================")
    
    device_found = check_device_manager()
    service_found = check_aura_service()
    sdk_found = check_aura_sdk()
    openrgb_found = check_openrgb()
    
    print("\nSummary:")
    print(f"- ASUS RGB devices found in Device Manager: {'Yes' if device_found else 'No'}")
    print(f"- ASUS AURA Service detected: {'Yes' if service_found else 'No'}")
    print(f"- ASUS AURA SDK installed: {'Yes' if sdk_found else 'No'}")
    print(f"- OpenRGB alternative available: {'Yes' if openrgb_found else 'No'}")
    
    if device_found or service_found or sdk_found:
        print("\nRESULT: Your system can likely recognize ASUS RGB controllers.")
        print("You can proceed with creating custom RGB control software.")
    else:
        print("\nRESULT: No ASUS RGB controllers detected.")
        print("Possible solutions:")
        print("1. Ensure ASUS Armoury Crate or AURA Sync is installed")
        print("2. Check if RGB headers are properly connected")
        print("3. Try installing OpenRGB as an alternative")

if __name__ == "__main__":
    main()