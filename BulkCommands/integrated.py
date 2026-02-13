"""
BulkCommands tool - Integrated mode for use with central connection manager.

This module provides BulkCommands functionality that integrates with the
central connection manager and main menu system.
"""

from . import main as bulk_main


def run_interactive(conn_manager):
    """
    Run BulkCommands in interactive mode with central connection manager.

    Args:
        conn_manager: Central ConnectionManager instance from main.py
    """
    # Use shared implementation from main.py
    bulk_main.run_bulk_commands(conn_manager)

    print("\nReturning to main menu...")
