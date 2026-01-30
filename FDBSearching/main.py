"""
This Python script automates the process of checking a MAC address against a local database and, if a match is found, connecting to a network device via SSH to gather further details about the connected port.

Key Features:
1. MAC Address Verification: Takes a user-input MAC address and verifies it against a predefined list of MAC addresses in 'macdatabase.txt'. The script focuses on the first three octets of the MAC address for verification.

2. Network Device Interaction: On a successful MAC address match, the script initiates an SSH connection to a network device using the last two octets of an IP address provided by the user. It constructs the full IP by prefixing the user input with a predefined IP structure ('10.192.').

3. Command Execution and Output Processing: After establishing the SSH connection, the script executes specific commands on the network device to retrieve and display information about the port to which the MAC address is connected. This includes fetching port information and descriptions.

Dependencies:
- Paramiko: A Python library used for handling SSH connections. The script uses Paramiko to connect to the network device, execute commands, and retrieve outputs.

Usage:
1. The user is prompted to enter a MAC address.
2. If the MAC address is found in the local database, the script asks for the last two octets of an IP address.
3. The script then reads SSH credentials from 'credentials.txt', establishes an SSH connection to the network device, and executes commands to retrieve port details.
4. The user is given the option to continue with a new MAC address or exit the program.

Note:
- Ensure 'macdatabase.txt' and 'credentials.txt' are properly set up and accessible.
- The IP structure and SSH commands are specific to the network setup and may need adjustments based on the network device's configuration.
"""

import paramiko
import csv
import os
import time
from datetime import datetime
import urllib.request
import json
import sys
import subprocess

VERSION = "1.0.0"

def get_fdb_info(ssh_client, switch_ip, fdb_cache, force_refresh=False):
    """
    Get FDB info from switch. Uses cache if available and less than 15 minutes old.
    Args:
        ssh_client: Active SSH client connection
        switch_ip: IP address of the switch
        fdb_cache: Dictionary storing cached FDB info
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        fdb_output: The FDB command output
    """
    current_time = time.time()
    cache_duration = 15 * 60  # 15 minutes in seconds

    # Check if we have cached data for this switch
    if switch_ip in fdb_cache and not force_refresh:
        cached_data = fdb_cache[switch_ip]
        time_since_cache = current_time - cached_data['timestamp']

        if time_since_cache < cache_duration:
            # Use cached data without prompting
            return cached_data['data']
        else:
            # Cache is stale, ask user if they want to refresh
            minutes_ago = int(time_since_cache / 60)
            user_input = input(f"\nFDB cache for {switch_ip} is {minutes_ago} minutes old. Refresh from switch (y/n)? ").lower()
            if user_input != 'y':
                return cached_data['data']

    # Fetch fresh FDB data
    print(f"Retrieving FDB info from {switch_ip}...")
    stdin, stdout, stderr = ssh_client.exec_command("show fdb")
    fdb_output = stdout.read().decode()

    # Cache the data
    fdb_cache[switch_ip] = {
        'data': fdb_output,
        'timestamp': current_time
    }

    return fdb_output


def get_ssh_connection(switch_ip, ssh_connections):
    """
    Get or create an SSH connection to the switch.
    Args:
        switch_ip: IP address of the switch
        ssh_connections: Dictionary storing active SSH connections

    Returns:
        ssh_client: Active SSH client connection
    """
    if switch_ip in ssh_connections:
        # Test if the connection is still active
        try:
            ssh_connections[switch_ip].exec_command("show system")
            return ssh_connections[switch_ip]
        except:
            # Connection is dead, remove and create new one
            try:
                ssh_connections[switch_ip].close()
            except:
                pass
            del ssh_connections[switch_ip]

    # Create new connection
    with open('credentials.txt', 'r') as file:
        ssh_username, ssh_password = file.read().strip().splitlines()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {switch_ip}...")
    ssh.connect(hostname=switch_ip, username=ssh_username, password=ssh_password, timeout=10, banner_timeout=10)

    # Store the connection
    ssh_connections[switch_ip] = ssh

    return ssh


def close_all_connections(ssh_connections):
    """Close all SSH connections."""
    for switch_ip, ssh_client in ssh_connections.items():
        try:
            ssh_client.close()
        except:
            pass
    ssh_connections.clear()


def load_camera_csv(csv_file='Byng Network Info & Tech Inventory - Cameras.csv'):
    """Load camera data from CSV file. Returns a list of dictionaries with camera info."""
    cameras = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Skip to line 30 where headers are (0-indexed, so skip 30 rows)
            for _ in range(30):
                next(reader)

            headers = next(reader)  # Read the header row

            # Read all camera data rows
            for row in reader:
                if len(row) > 0 and row[0]:  # Skip empty rows
                    cameras.append({
                        'server_name': row[0] if len(row) > 0 else '',
                        'device_name': row[1] if len(row) > 1 else '',
                        'ip_address': row[2] if len(row) > 2 else '',
                        'model': row[3] if len(row) > 3 else '',
                        'mac_address': row[4] if len(row) > 4 else '',
                        'switch_port': row[5] if len(row) > 5 else '',
                    })
    except Exception as e:
        print(f"Error loading CSV file: {e}")

    return cameras

def find_camera_by_mac(mac_address, cameras):
    """Search for camera by MAC address in the loaded camera data."""
    # Normalize MAC address for comparison (remove colons/hyphens, lowercase)
    normalized_search_mac = mac_address.replace(':', '').replace('-', '').lower()

    for camera in cameras:
        normalized_csv_mac = camera['mac_address'].replace(':', '').replace('-', '').lower()
        if normalized_search_mac == normalized_csv_mac:
            return camera

    return None

def check_mac_database(user_mac, database_file='macdatabase.txt'):
       # Remove colons if present and take the first 6 characters (first three octets) of the MAC address
       formatted_mac = user_mac.replace(':', '').lower()[:6]

       with open(database_file, 'r', encoding='utf-8') as file:
           for line in file:
               # Extract the MAC prefix from the database line and compare
               db_mac_prefix = line.split()[0].replace(':', '').lower()[:6]
               if formatted_mac == db_mac_prefix:
                   print(f"Database match found: {line.strip()}")
                   return True  # Return True if a match is found
       return False  # Return False if no match is found

def mode1_mac_search(cameras, fdb_cache, ssh_connections):
    """Mode 1: Start with MAC address and search switches."""
    while True:
        user_mac = input("Enter the MAC address: ").lower()
        if not check_mac_database(user_mac):  # Check MAC address in the database
            print("No match found in the database.")
            continue

        # Look up camera info from CSV
        camera_info = find_camera_by_mac(user_mac, cameras)
        if camera_info:
            print(f"\nCamera Found in Inventory:")
            print(f"  Device Name: {camera_info['device_name']}")
            print(f"  IP Address: {camera_info['ip_address']}")
            print(f"  Model: {camera_info['model']}")
            print(f"  MAC Address: {camera_info['mac_address']}")
            print(f"  Switch/Port: {camera_info['switch_port']}\n")
        else:
            print("\nCamera not found in inventory CSV.\n")

        while True:
            ip_octets = input("Enter the last 2 octets of the IP address: ")
            full_ip = f"10.10.{ip_octets}"

            try:
                # Get or create SSH connection
                ssh = get_ssh_connection(full_ip, ssh_connections)

                # Get FDB info (cached or fresh)
                switch_output = get_fdb_info(ssh, full_ip, fdb_cache)

                matching_line = None
                formatted_user_mac = user_mac.replace(':', '').lower()

                print("\nSearching FDB output:")
                for line in switch_output.splitlines():
                    print(f"  {line}")
                    if formatted_user_mac in line.replace(':', '').lower():
                        matching_line = line

                # Display results and get port info
                if matching_line:
                    print(f"\nMatching line: {matching_line}")
                    port_number = matching_line.split()[-1]

                    # Execute and display port information command
                    print("\nshow ports # information")
                    stdin, stdout, stderr = ssh.exec_command(f"show ports {port_number} information")
                    port_info = stdout.read().decode()
                    print(port_info)

                    # Execute and display show lldp neighbors command
                    print("show lldp neighbors")
                    stdin, stdout, stderr = ssh.exec_command(f"show lldp neighbors")
                    lldp_neighbors = stdout.read().decode()
                    print(lldp_neighbors)

                    # Execute and display port description command
                    print("show ports # description\n")
                    stdin, stdout, stderr = ssh.exec_command(f"show ports {port_number} description")
                    port_description = stdout.read().decode()
                    print(port_description)
                else:
                    print("\nMAC address not found in the switch's FDB.")

                # Ask to continue with the same MAC address
                user_choice = input("Do you want to try another IP for this MAC address (y/n)? ").lower()
                if user_choice != 'y':
                    break  # Break the inner loop to ask for a new MAC address

            except Exception as e:
                print(f"An error occurred: {e}")

        # Ask if the user wants to check another MAC address
        continue_program = input("Do you want to check another MAC address (y/n)? ").lower()
        if continue_program != 'y':
            break  # Exit to main menu


def mode2_port_search(cameras, fdb_cache, ssh_connections):
    """Mode 2: Start with switch/port and identify device via FDB."""
    while True:
        switch_ip = input("Enter the switch IP address (e.g., 10.10.1.1): ")
        port_number = input("Enter the port number: ")

        try:
            # Get or create SSH connection
            ssh = get_ssh_connection(switch_ip, ssh_connections)

            # Get FDB info (cached or fresh)
            fdb_output = get_fdb_info(ssh, switch_ip, fdb_cache)

            # Extract MAC addresses from the port
            port_macs = []

            print("\nSearching FDB output:")
            for line in fdb_output.splitlines():
                print(f"  {line}")
                if port_number in line:
                    # Extract MAC address from the line (usually first column after port info)
                    parts = line.split()
                    if len(parts) > 0:
                        # Try to extract MAC address from the line
                        mac_candidate = parts[0]
                        # Check if it looks like a MAC address
                        if ':' in mac_candidate or '-' in mac_candidate or len(mac_candidate.replace(' ', '')) == 12:
                            port_macs.append(mac_candidate)

            if port_macs:
                print(f"\nFound {len(port_macs)} MAC address(es) on port {port_number}:")

                # Show port description
                print(f"\nshow port {port_number} description")
                stdin, stdout, stderr = ssh.exec_command(f"show ports {port_number} description")
                port_description = stdout.read().decode()
                print(port_description)

                for mac in port_macs:
                    camera = find_camera_by_mac(mac, cameras)
                    if camera:
                        print(f"\n  MAC: {mac}")
                        print(f"    Device Name (Column B): {camera['device_name']}")
                        print(f"    IP Address (Column C): {camera['ip_address']}")
                        print(f"    MAC Address (Column E): {camera['mac_address']} (verified)")
                    else:
                        print(f"\n  MAC: {mac}")
                        print(f"    Not found in inventory")
            else:
                print(f"No MAC addresses found on port {port_number}")

        except Exception as e:
            print(f"An error occurred: {e}")

        # Ask if user wants to continue
        continue_program = input("\nDo you want to check another port (y/n)? ").lower()
        if continue_program != 'y':
            break  # Exit to main menu




def check_for_updates():
    """Check for updates using the central update script."""
    try:
        # Get the parent directory (CustomTools root)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        update_script = os.path.join(parent_dir, "update.py")

        if not os.path.exists(update_script):
            return  # Update script not found, skip update check

        # Run update script in check-only mode
        result = subprocess.run(
            [sys.executable, update_script, "--check-only"],
            capture_output=True,
            timeout=10
        )

        # Display update check output regardless of exit code
        if result.stdout:
            print(result.stdout.decode())
    except Exception as e:
        # If update check fails, just continue
        pass


def main():
    # Display version
    print(f"FDB Search Program v{VERSION}")

    # Check for updates on startup
    check_for_updates()

    # Load camera data once at startup
    cameras = load_camera_csv()
    if not cameras:
        print("Warning: Could not load camera CSV file. Some features may not work.")

    # Initialize caching and connection management
    fdb_cache = {}
    ssh_connections = {}

    try:
        while True:
            print("\n" + "="*50)
            print("FDB Search Program - Mode Selection")
            print("="*50)
            print("1. Mode 1: Start with MAC address → Search Switches")
            print("2. Mode 2: Start with Switch/Port → Identify Device")
            print("3. Exit")
            print("="*50)

            choice = input("Select mode (1/2/3): ").strip()

            if choice == '1':
                mode1_mac_search(cameras, fdb_cache, ssh_connections)
            elif choice == '2':
                mode2_port_search(cameras, fdb_cache, ssh_connections)
            elif choice == '3':
                print("Exiting the program. Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
    finally:
        # Clean up all SSH connections
        close_all_connections(ssh_connections)

if __name__ == "__main__":
    main()