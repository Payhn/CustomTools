#!/usr/bin/env python3
"""
BulkCommands - Execute a list of commands on multiple network switches with comprehensive logging.

This module provides both standalone and integrated modes:
- Standalone: Run directly with local SSH connection management
- Integrated: Called from central menu with shared ConnectionManager
"""

import sys
from pathlib import Path
import csv
import paramiko
import socket
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import credentials


# ============================================================================
# CSV MANAGEMENT FUNCTIONS
# ============================================================================

def get_csv_path(filename):
    """Get absolute path to CSV file in BulkCommands directory."""
    script_dir = Path(__file__).parent
    return script_dir / filename


def create_switches_template(path):
    """Create switches.csv template file."""
    template = """hostname
10.10.1.1
10.10.1.2
"""
    path.write_text(template)


def create_commands_template(path):
    """Create commands.csv template file."""
    template = """command
show version
show system
"""
    path.write_text(template)


def ensure_csv_files():
    """
    Ensure CSV files exist, create templates if missing.

    Returns:
        True if both files exist and have content, False otherwise
    """
    switches_csv = get_csv_path("switches.csv")
    commands_csv = get_csv_path("commands.csv")

    missing_files = []

    if not switches_csv.exists():
        create_switches_template(switches_csv)
        missing_files.append("switches.csv")

    if not commands_csv.exists():
        create_commands_template(commands_csv)
        missing_files.append("commands.csv")

    if missing_files:
        print(f"\n⚠️  Template files created: {', '.join(missing_files)}")
        print(f"📁 Location: {switches_csv.parent}")
        print("✏️  Please edit these files and run again.")
        return False

    return True


def load_csv_column(csv_path, column_name):
    """
    Load single column from CSV file.

    Args:
        csv_path: Path to CSV file
        column_name: Name of column to read

    Returns:
        List of values from column (empty rows skipped)

    Raises:
        ValueError: If file is invalid or empty
    """
    items = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check header exists
            if not reader.fieldnames or column_name not in reader.fieldnames:
                raise ValueError(f"Column '{column_name}' not found in {csv_path}")

            # Read items
            for row in reader:
                value = row[column_name].strip()
                if value:  # Skip empty rows
                    items.append(value)

    except csv.Error as e:
        raise ValueError(f"CSV parsing error in {csv_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading {csv_path}: {e}")

    if not items:
        raise ValueError(f"No items found in {csv_path}")

    return items


# ============================================================================
# LOGGING INFRASTRUCTURE
# ============================================================================

def get_logs_dir():
    """Get or create the Logs directory."""
    script_dir = Path(__file__).parent
    logs_dir = script_dir / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_log_file_path(switch):
    """
    Get log file path for current session.
    Creates directories as needed.

    Args:
        switch: Switch hostname or IP

    Returns:
        Path object for log file
    """
    logs_dir = get_logs_dir()

    # Sanitize switch name (remove/replace problematic characters)
    switch_safe = switch.replace("/", "_").replace("\\", "_").replace(":", "_")
    switch_dir = logs_dir / switch_safe

    # Create switch directory
    switch_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = switch_dir / f"{timestamp}.txt"

    return log_file


def write_log_header(log_file, switch, timestamp_str):
    """Write session header to log file."""
    header = f"""================================================================================
BulkCommands Session Log
Switch: {switch}
Session Start: {timestamp_str}
================================================================================

"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(header)


def log_command_execution(log_file, command, output, error, exec_time, status):
    """
    Append command execution result to log file.

    Args:
        log_file: Path to log file
        command: Command that was executed
        output: stdout output
        error: stderr output
        exec_time: Execution time in seconds
        status: Status string (Success, Error, etc.)
    """
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] Executing: {command}\n"
    entry += "-" * 80 + "\n"
    entry += output

    if error:
        entry += f"\nERROR: {error}"

    entry += "\n" + "-" * 80 + "\n"
    entry += f"Execution Time: {exec_time:.2f}s\n"
    entry += f"Status: {status}\n\n"

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(entry)


def write_log_footer(log_file, total_commands, successful, errors):
    """Write session footer to log file."""
    footer = f"""================================================================================
Session End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Commands: {total_commands} | Successful: {successful} | Errors: {errors}
================================================================================
"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(footer)


# ============================================================================
# COMMAND EXECUTION
# ============================================================================

def execute_command(ssh, command, timeout=30):
    """
    Execute command on SSH connection with timeout.

    Args:
        ssh: Paramiko SSH client
        command: Command to execute
        timeout: Command timeout in seconds

    Returns:
        Tuple of (output, error, success, exec_time)
    """
    start_time = time.time()

    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)

        # Read output
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')

        exec_time = time.time() - start_time
        return output, error, True, exec_time

    except socket.timeout:
        exec_time = time.time() - start_time
        return "", "Command execution timed out", False, exec_time
    except Exception as e:
        exec_time = time.time() - start_time
        return "", str(e), False, exec_time


def process_switch(conn_manager, switch, commands, log_file):
    """
    Execute all commands on a switch and log results.

    Args:
        conn_manager: Connection manager instance
        switch: Switch hostname or IP
        commands: List of commands to execute
        log_file: Path to log file

    Returns:
        Dictionary with stats: {total, success, errors, connection_failed}
    """
    stats = {
        'total': 0,
        'success': 0,
        'errors': 0,
        'connection_failed': False
    }

    try:
        # Get connection
        ssh = conn_manager.get_connection(switch)

        # Write session header
        write_log_header(log_file, switch, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Execute each command
        for idx, command in enumerate(commands, 1):
            stats['total'] += 1

            try:
                output, error, success, exec_time = execute_command(ssh, command)

                if success and not error:
                    status = "Success"
                    stats['success'] += 1
                    print(f"  [{idx}/{len(commands)}] {command}... ✓")
                elif success:
                    status = "Completed with errors"
                    stats['errors'] += 1
                    print(f"  [{idx}/{len(commands)}] {command}... ⚠️")
                else:
                    status = "Failed"
                    stats['errors'] += 1
                    print(f"  [{idx}/{len(commands)}] {command}... ✗")

                log_command_execution(log_file, command, output, error, exec_time, status)

            except Exception as e:
                stats['errors'] += 1
                print(f"  [{idx}/{len(commands)}] {command}... ✗")
                log_command_execution(log_file, command, "", str(e), 0, "Failed")

        # Write footer
        write_log_footer(log_file, stats['total'], stats['success'], stats['errors'])

    except Exception as e:
        stats['connection_failed'] = True
        print(f"  ✗ Connection failed: {str(e)}")

        # Write error to log
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"Connection Error: {str(e)}\n")
        except:
            pass

    return stats


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_bulk_commands(conn_manager):
    """
    Main entry point for BulkCommands tool.

    Args:
        conn_manager: Connection manager instance (local or central)
    """
    print("\n" + "=" * 80)
    print("BulkCommands Tool - Execute Commands on Multiple Switches")
    print("=" * 80)

    # Step 1: Ensure CSV files exist
    print("\n📋 Checking CSV files...")
    if not ensure_csv_files():
        return

    # Step 2: Load CSV data
    print("📖 Loading configuration...")
    try:
        switches_csv = get_csv_path("switches.csv")
        commands_csv = get_csv_path("commands.csv")

        switches = load_csv_column(switches_csv, "hostname")
        commands = load_csv_column(commands_csv, "command")

        print(f"✓ Loaded {len(switches)} switch(es) and {len(commands)} command(s)")
    except ValueError as e:
        print(f"❌ Error loading CSV files: {e}")
        return

    # Step 3: Create Logs directory
    get_logs_dir()

    # Step 4: Process each switch
    print("\n" + "=" * 80)
    print("🚀 Starting command execution...")
    print("=" * 80)

    overall_stats = {
        'total_switches': len(switches),
        'processed': 0,
        'connection_failures': 0,
        'total_commands': 0,
        'total_success': 0,
        'total_errors': 0
    }

    for switch_idx, switch in enumerate(switches, 1):
        print(f"\n[{switch_idx}/{len(switches)}] Processing: {switch}")
        print("-" * 80)

        # Get log file path for this session
        log_file = get_log_file_path(switch)

        # Process switch
        stats = process_switch(conn_manager, switch, commands, log_file)

        # Update overall stats
        overall_stats['processed'] += 1
        overall_stats['total_commands'] += stats['total']
        overall_stats['total_success'] += stats['success']
        overall_stats['total_errors'] += stats['errors']

        if stats['connection_failed']:
            overall_stats['connection_failures'] += 1
        else:
            print(f"📝 Logged to: {log_file}")

    # Step 5: Print summary
    print("\n" + "=" * 80)
    print("BulkCommands Execution Summary")
    print("=" * 80)
    print(f"Switches Processed: {overall_stats['processed']}/{overall_stats['total_switches']}")
    print(f"Connection Failures: {overall_stats['connection_failures']}")
    print(f"Total Commands Executed: {overall_stats['total_commands']}")
    print(f"  ✓ Successful: {overall_stats['total_success']}")
    print(f"  ✗ Errors: {overall_stats['total_errors']}")
    print(f"📁 Logs Location: {get_logs_dir()}")
    print("=" * 80)


# ============================================================================
# LOCAL CONNECTION MANAGER (for standalone mode)
# ============================================================================

class LocalConnectionManager:
    """Local SSH connection manager for standalone mode."""

    def __init__(self, username, password):
        """Initialize with credentials."""
        self.connections = {}
        self.username = username
        self.password = password

    def get_connection(self, host):
        """
        Get or create SSH connection to host.

        Args:
            host: Hostname or IP address

        Returns:
            Paramiko SSH client

        Raises:
            Exception: If connection fails
        """
        # Return existing connection if available
        if host in self.connections:
            return self.connections[host]

        # Create new connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=host,
                username=self.username,
                password=self.password,
                timeout=10,
                banner_timeout=10
            )

            # Cache connection
            self.connections[host] = ssh
            return ssh

        except Exception as e:
            raise Exception(f"Failed to connect to {host}: {str(e)}")

    def close_all(self):
        """Close all SSH connections."""
        for ssh in self.connections.values():
            try:
                ssh.close()
            except:
                pass
        self.connections.clear()


# ============================================================================
# STANDALONE ENTRY POINT
# ============================================================================

def main():
    """Standalone mode entry point."""
    try:
        # Load credentials
        username, password = credentials.load_credentials(create_if_missing=True)

        # Create connection manager
        conn_manager = LocalConnectionManager(username, password)

        try:
            # Run tool
            run_bulk_commands(conn_manager)
        finally:
            # Clean up connections
            conn_manager.close_all()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
