#!/usr/bin/env python3
"""
CustomTools Main Entry Point
Centralized credentials, connection management, and tool orchestration.

This is the main entry point for all CustomTools. It handles:
- Credential management and validation
- SSH connection pooling and reuse
- Tool selection and execution
- Interactive menu system that maintains state between tool runs
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import credentials
import paramiko

VERSION = "1.0.0"


class ConnectionManager:
    """
    Manages SSH connections to switches.
    Maintains a pool of connections and reuses them across tool executions.
    """

    def __init__(self, username: str, password: str):
        """
        Initialize the connection manager.

        Args:
            username: SSH username
            password: SSH password
        """
        self.username = username
        self.password = password
        self.connections: Dict[str, paramiko.SSHClient] = {}

    def get_connection(self, host: str, timeout: int = 10) -> paramiko.SSHClient:
        """
        Get or create an SSH connection to the specified host.

        Args:
            host: Hostname or IP address
            timeout: Connection timeout in seconds

        Returns:
            paramiko.SSHClient: Active SSH connection

        Raises:
            Exception: If connection fails
        """
        # Check if we have an active connection
        if host in self.connections:
            try:
                # Test if the connection is still active
                self.connections[host].exec_command("show system")
                return self.connections[host]
            except Exception:
                # Connection is dead, remove it
                try:
                    self.connections[host].close()
                except Exception:
                    pass
                del self.connections[host]

        # Create new connection
        print(f"Connecting to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=host,
                username=self.username,
                password=self.password,
                timeout=timeout,
                banner_timeout=timeout,
            )
            self.connections[host] = ssh
            print(f"Connected to {host}")
            return ssh
        except Exception as e:
            print(f"Failed to connect to {host}: {e}")
            raise

    def list_connections(self) -> list:
        """Get list of active connection hosts."""
        return list(self.connections.keys())

    def close_all(self) -> None:
        """Close all active SSH connections."""
        for host, ssh_client in self.connections.items():
            try:
                ssh_client.close()
                print(f"Closed connection to {host}")
            except Exception:
                pass
        self.connections.clear()

    def close_connection(self, host: str) -> None:
        """Close a specific SSH connection."""
        if host in self.connections:
            try:
                self.connections[host].close()
                del self.connections[host]
                print(f"Closed connection to {host}")
            except Exception as e:
                print(f"Error closing connection to {host}: {e}")


class ToolRunner:
    """Handles execution of available tools."""

    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager

    def run_fdb_searching(self) -> None:
        """Run the FDB Searching tool with maintained connections."""
        try:
            # Import the FDB searching integrated module
            from FDBSearching import integrated as fdb_integrated

            # Run with our connection manager
            fdb_integrated.run_interactive(self.conn_manager)
        except ImportError as e:
            print(f"Error: FDBSearching module not found: {e}")
        except Exception as e:
            print(f"Error running FDBSearching: {e}")

    def run_create_backup(self) -> None:
        """Run the Create Backup tool with maintained connections."""
        print("\n--- Create Backup Tool ---")
        print("Feature not yet implemented.")
        print("This tool will:")
        print("  - Connect to a list of switches")
        print("  - Get config backups")
        print("  - Log device information")
        input("\nPress Enter to return to main menu...")

    def run_bulk_update(self) -> None:
        """Run the Bulk Update tool with maintained connections."""
        try:
            from BulkCommands import integrated
            integrated.run_interactive(self.conn_manager)
        except ImportError as e:
            print(f"Error: BulkCommands module not found: {e}")
        except Exception as e:
            print(f"Error running BulkCommands: {e}")
            import traceback
            traceback.print_exc()

    def run_self_lookup(self) -> None:
        """Run the Self Lookup tool with maintained connections."""
        print("\n--- Self Lookup Tool ---")
        print("Feature not yet implemented.")
        print("This tool will:")
        print("  - Analyze local network interfaces")
        print("  - Allow searching for devices on the network")
        print("  - Find which switch a device is connected to")
        input("\nPress Enter to return to main menu...")

    def run_interactive_session(self) -> None:
        """Allow user to have an interactive session with a maintained connection."""
        print("\n--- Interactive Session ---")

        # Show available connections
        active_connections = self.conn_manager.list_connections()
        if active_connections:
            print(f"Active connections: {', '.join(active_connections)}")
        else:
            print("No active connections. Create one first by running a tool.")
            return

        host = input(
            "Enter host to connect to (or press Enter to create new): "
        ).strip()

        if not host:
            host = input("Enter host IP/address: ").strip()
            if not host:
                return

        try:
            ssh = self.conn_manager.get_connection(host)
            print(f"\nConnected to {host}. Type 'exit' to return to menu.\n")

            while True:
                try:
                    command = input(f"{host}> ").strip()
                    if command.lower() == "exit":
                        break
                    if not command:
                        continue

                    stdin, stdout, stderr = ssh.exec_command(command)
                    output = stdout.read().decode()
                    errors = stderr.read().decode()

                    if output:
                        print(output)
                    if errors:
                        print(f"Error: {errors}")
                except KeyboardInterrupt:
                    print("\nInterrupted by user")
                    break
                except Exception as e:
                    print(f"Command error: {e}")

        except Exception as e:
            print(f"Error establishing interactive session: {e}")

        input("\nPress Enter to return to main menu...")


class MainMenu:
    """Main menu and program flow controller."""

    def __init__(self, username: str, password: str):
        self.conn_manager = ConnectionManager(username, password)
        self.tool_runner = ToolRunner(self.conn_manager)

    def display_menu(self) -> None:
        """Display the main menu."""
        active_conns = self.conn_manager.list_connections()
        conn_status = f" [{len(active_conns)} active]" if active_conns else ""

        print("\n" + "=" * 60)
        print(f"CustomTools v{VERSION} - Main Menu{conn_status}")
        print("=" * 60)
        print("\nAvailable Tools:")
        print("  1. FDB Searching    - Search for MAC addresses on switches")
        print("  2. Create Backup    - Backup switch configurations")
        print("  3. Bulk Update      - Run commands on multiple switches")
        print("  4. Self Lookup      - Find your device on the network")
        print("\nConnection Management:")
        print("  5. Interactive Session   - Direct access to a switch")
        print("  6. List Connections      - Show active connections")
        print("  7. Close Connection      - Disconnect from a switch")
        print("\nProgram Control:")
        print("  8. Exit - Close all connections and exit")
        print("=" * 60)

    def run(self) -> None:
        """Run the main program loop."""
        print(f"CustomTools v{VERSION}")
        print(f"Logged in as: {self.conn_manager.username}")

        while True:
            self.display_menu()
            choice = input("Select option (1-8): ").strip()

            if choice == "1":
                self.tool_runner.run_fdb_searching()
            elif choice == "2":
                self.tool_runner.run_create_backup()
            elif choice == "3":
                self.tool_runner.run_bulk_update()
            elif choice == "4":
                self.tool_runner.run_self_lookup()
            elif choice == "5":
                self.tool_runner.run_interactive_session()
            elif choice == "6":
                self.show_connections()
            elif choice == "7":
                self.close_connection()
            elif choice == "8":
                self.exit_program()
                break
            else:
                print("Invalid option. Please select 1-8.")

    def show_connections(self) -> None:
        """Show active connections."""
        active = self.conn_manager.list_connections()
        print("\n--- Active Connections ---")
        if active:
            for i, host in enumerate(active, 1):
                print(f"  {i}. {host}")
        else:
            print("  No active connections")
        input("\nPress Enter to return to main menu...")

    def close_connection(self) -> None:
        """Close a specific connection."""
        active = self.conn_manager.list_connections()
        if not active:
            print("\nNo active connections to close")
            input("Press Enter to return to main menu...")
            return

        print("\n--- Close Connection ---")
        for i, host in enumerate(active, 1):
            print(f"  {i}. {host}")

        try:
            choice = input("Select connection to close (number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(active):
                self.conn_manager.close_connection(active[idx])
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")

        input("\nPress Enter to return to main menu...")

    def exit_program(self) -> None:
        """Clean shutdown."""
        print("\n--- Shutting Down ---")
        print("Closing all connections...")
        self.conn_manager.close_all()
        print("Goodbye!")


def ensure_credentials() -> Tuple[str, str]:
    """
    Ensure credentials are available.
    Creates template if missing, loads from file, and validates.

    Returns:
        Tuple of (username, password)

    Raises:
        Exception: If credentials cannot be loaded
    """
    try:
        username, password = credentials.load_credentials(create_if_missing=True)
        return username, password
    except FileNotFoundError as e:
        print(f"\nCredential Setup Required:")
        print(f"  {e}")
        creds_path = credentials.get_credentials_path()
        print(f"\nPlease edit: {creds_path}")
        print("  Line 1: username")
        print("  Line 2: password")
        print("\nThen run this program again.")
        sys.exit(1)
    except ValueError as e:
        print(f"\nCredential Error:")
        print(f"  {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print(f"CustomTools v{VERSION}")
    print("=" * 60)

    # Ensure credentials exist and are valid
    print("\nChecking credentials...")
    username, password = ensure_credentials()
    print(f"Credentials loaded for user: {username}")

    # Start main menu
    menu = MainMenu(username, password)
    try:
        menu.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        menu.conn_manager.close_all()
        sys.exit(0)


if __name__ == "__main__":
    main()
