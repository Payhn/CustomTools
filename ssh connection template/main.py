"""
Network Switch SSH Connection Template

This module provides a reusable template for connecting to network switches and executing commands.
It handles SSH credential management, connection pooling, and graceful shutdown.

Key Features:
1. SSH Connection Management: Maintains a pool of persistent SSH connections with health checks
2. Credential Management: Reads SSH credentials from 'credentials.txt'
3. Logging System: Comprehensive logging to console and file
4. Graceful Shutdown: Automatically closes all connections on exit

Dependencies:
- Paramiko: SSH library for network device connections

Usage:
- Extend this template by implementing your specific logic in the main() function
- Use get_ssh_connection() to get a connection to a switch
- All connections are automatically cleaned up at exit
"""

import paramiko
import os
import logging
import sys

VERSION = "0.0.1"


def setup_logging(log_level=logging.INFO):
    """
    Configure logging to both console and file.

    Args:
        log_level: logging level (default: logging.INFO)
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler('network_tool.log')
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger



def read_ssh_credentials(cred_file='credentials.txt'):
    """
    Read SSH credentials from credentials.txt.

    File format:
        Line 1: username
        Line 2: password

    Args:
        cred_file: Path to credentials file

    Returns:
        Tuple of (username, password)

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials file is invalid
    """
    logger = logging.getLogger(__name__)

    try:
        with open(cred_file, 'r') as file:
            lines = file.read().strip().splitlines()

        if len(lines) < 2:
            raise ValueError("Credentials file must contain username and password on separate lines")

        username, password = lines[0], lines[1]
        logger.debug(f"Successfully read SSH credentials for user: {username}")
        return username, password

    except FileNotFoundError:
        logger.error(f"Credentials file not found: {cred_file}")
        raise
    except Exception as e:
        logger.error(f"Error reading credentials file: {e}")
        raise


def get_ssh_connection(switch_ip, ssh_connections):
    """
    Get or create an SSH connection to the switch.

    Maintains a pool of connections and tests them for health before returning.
    If a connection is dead, it's removed and a new one is created.

    Args:
        switch_ip: IP address of the switch
        ssh_connections: Dictionary storing active SSH connections

    Returns:
        ssh_client: Active SSH client connection

    Raises:
        Exception: If SSH connection fails
    """
    logger = logging.getLogger(__name__)

    if switch_ip in ssh_connections:
        # Test if the connection is still active
        try:
            logger.debug(f"Testing existing connection to {switch_ip}")
            ssh_connections[switch_ip].exec_command("show system")
            logger.debug(f"Reusing existing connection to {switch_ip}")
            return ssh_connections[switch_ip]
        except Exception as e:
            # Connection is dead, remove and create new one
            logger.warning(f"Connection to {switch_ip} is dead: {e}")
            try:
                ssh_connections[switch_ip].close()
            except:
                pass
            del ssh_connections[switch_ip]

    # Create new connection
    logger.info(f"Establishing new SSH connection to {switch_ip}")

    try:
        username, password = read_ssh_credentials()
    except Exception as e:
        logger.error(f"Failed to read credentials: {e}")
        raise

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=switch_ip,
            username=username,
            password=password,
            timeout=10,
            banner_timeout=10
        )
        logger.info(f"Successfully connected to {switch_ip}")
    except Exception as e:
        logger.error(f"Failed to connect to {switch_ip}: {e}")
        raise

    # Store the connection
    ssh_connections[switch_ip] = ssh
    return ssh


def close_all_connections(ssh_connections):
    """
    Close all active SSH connections.

    Args:
        ssh_connections: Dictionary of active SSH connections
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Closing {len(ssh_connections)} SSH connection(s)")

    for switch_ip, ssh_client in ssh_connections.items():
        try:
            ssh_client.close()
            logger.debug(f"Closed connection to {switch_ip}")
        except Exception as e:
            logger.warning(f"Error closing connection to {switch_ip}: {e}")

    ssh_connections.clear()




def main():
    """Main entry point for the network switch tool."""
    # Initialize logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Display version
    logger.info(f"Network Switch Tool v{VERSION}")

    # Initialize connection management
    ssh_connections = {}

    try:
        # TODO: Implement your custom logic here
        # Use get_ssh_connection(switch_ip, ssh_connections) to get a connection
        # Example:
        # ssh = get_ssh_connection("10.10.1.1", ssh_connections)
        # stdin, stdout, stderr = ssh.exec_command("your command here")
        # output = stdout.read().decode()
        logger.info("Tool started. Ready to use connections.")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up all SSH connections
        close_all_connections(ssh_connections)
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
