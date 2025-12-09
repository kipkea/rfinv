# rpi_camera_controller_opencv/services/network_service.py

import subprocess
import re

class NetworkService:
    def __init__(self):
        pass

    def get_network_status(self) -> dict:
        """
        Retrieves the current network status (Wi-Fi and Ethernet).
        
        :return: Dictionary with status information.
        """
        status = {'wifi': 'Unknown', 'ethernet': 'Unknown', 'ip_address': 'N/A'}
        
        # Simulate network status retrieval (requires actual RPi OS with nmcli)
        try:
            # Check Wi-Fi status
            wifi_output = subprocess.run(['nmcli', 'radio', 'wifi'], capture_output=True, text=True, timeout=5)
            if 'enabled' in wifi_output.stdout.lower():
                status['wifi'] = 'Enabled'
            elif 'disabled' in wifi_output.stdout.lower():
                status['wifi'] = 'Disabled'
            
            # Get active connections and IP
            conn_output = subprocess.run(['nmcli', '-t', '-f', 'TYPE,STATE,IP4_ADDRESS', 'device', 'show'], capture_output=True, text=True, timeout=5)
            
            for line in conn_output.stdout.splitlines():
                parts = line.split(':')
                if len(parts) >= 3:
                    dev_type, state, ip_addr = parts[0], parts[1], parts[2]
                    if state == 'connected':
                        if dev_type == 'wifi':
                            status['wifi'] = 'Connected'
                        elif dev_type == 'ethernet':
                            status['ethernet'] = 'Connected'
                        
                        if ip_addr and ip_addr != 'N/A':
                            # Extract only the IP address part
                            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_addr)
                            if ip_match:
                                status['ip_address'] = ip_match.group(1)
                                
        except FileNotFoundError:
            status['error'] = "nmcli command not found. (Simulated environment)"
        except subprocess.TimeoutExpired:
            status['error'] = "nmcli command timed out."
        except Exception as e:
            status['error'] = f"Error retrieving network status: {e}"

        return status

    def set_wifi_connection(self, ssid: str, password: str) -> dict:
        """
        Simulates setting up a Wi-Fi connection using nmcli.
        
        :param ssid: Wi-Fi network name.
        :param password: Wi-Fi password.
        :return: Dictionary with status and message.
        """
        # NOTE: This requires sudo privileges on the actual RPi.
        # Command: sudo nmcli device wifi connect <ssid> password <password>
        
        print(f"SIMULATING: Setting Wi-Fi connection to SSID: {ssid}")
        
        # In a real environment, you would execute the command:
        # try:
        #     subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password], check=True)
        #     return {'success': True, 'message': f"Successfully connected to {ssid} (Requires sudo on RPi)."}
        # except subprocess.CalledProcessError as e:
        #     return {'success': False, 'message': f"Failed to connect to {ssid}: {e.stderr.strip()}"}
        
        return {'success': True, 'message': f"SIMULATED: Attempted to connect to {ssid}. (Requires sudo on RPi)"}

    def set_static_ip(self, interface: str, ip_address: str, gateway: str, dns: str) -> dict:
        """
        Simulates setting a static IP address using nmcli.
        
        :param interface: Network interface (e.g., eth0, wlan0).
        :param ip_address: Static IP address/CIDR.
        :param gateway: Gateway IP address.
        :param dns: DNS server IP address.
        :return: Dictionary with status and message.
        """
        # NOTE: This requires sudo privileges on the actual RPi.
        
        print(f"SIMULATING: Setting static IP for {interface} to {ip_address}")
        
        # In a real environment, you would execute the commands:
        # subprocess.run(['sudo', 'nmcli', 'con', 'mod', interface, 'ipv4.addresses', ip_address], check=True)
        # subprocess.run(['sudo', 'nmcli', 'con', 'mod', interface, 'ipv4.gateway', gateway], check=True)
        # subprocess.run(['sudo', 'nmcli', 'con', 'mod', interface, 'ipv4.dns', dns], check=True)
        # subprocess.run(['sudo', 'nmcli', 'con', 'mod', interface, 'ipv4.method', 'manual'], check=True)
        # subprocess.run(['sudo', 'nmcli', 'con', 'up', interface], check=True)
        
        return {'success': True, 'message': f"SIMULATED: Static IP set for {interface} to {ip_address}. (Requires sudo on RPi)"}

# Example Usage (for testing purposes)
if __name__ == '__main__':
    net_service = NetworkService()
    status = net_service.get_network_status()
    print(f"Current Network Status: {status}")
    
    # Test setting Wi-Fi (simulated)
    # result = net_service.set_wifi_connection("MyWifi", "password123")
    # print(f"Wi-Fi Set Result: {result}")
