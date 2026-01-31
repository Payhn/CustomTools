#!/usr/bin/env python3
"""
Centralized credentials management for CustomTools.
Handles loading, creating, and validating credentials.
Place credentials.txt in the same directory as this file (CustomTools root).
"""

import os
from pathlib import Path


def get_credentials_path():
    """
    Get the path to the credentials.txt file.
    Located in the CustomTools root directory.
    """
    script_dir = Path(__file__).parent
    return script_dir / "credentials.txt"


def credentials_exist():
    """Check if credentials file exists."""
    return get_credentials_path().exists()


def create_credentials_template():
    """
    Create a credentials template file if it doesn't exist.
    Returns True if created, False if already existed.
    """
    creds_path = get_credentials_path()

    if creds_path.exists():
        return False

    template = """username
password"""

    try:
        creds_path.write_text(template)
        print(f"Created credentials template at: {creds_path}")
        print("Please edit this file with your actual credentials.")
        return True
    except Exception as e:
        print(f"Error creating credentials file: {e}")
        return False


def load_credentials(create_if_missing=True):
    """
    Load SSH credentials from credentials.txt file.

    Args:
        create_if_missing: If True, create template file if it doesn't exist

    Returns:
        tuple: (username, password)

    Raises:
        FileNotFoundError: If credentials.txt doesn't exist and create_if_missing=False
        ValueError: If credentials file is improperly formatted
    """
    creds_path = get_credentials_path()

    # Create template if missing and allowed
    if not creds_path.exists():
        if create_if_missing:
            create_credentials_template()
            raise FileNotFoundError(
                f"Credentials template created at {creds_path}. "
                "Please fill it with your credentials and run again."
            )
        else:
            raise FileNotFoundError(
                f"Credentials file not found at {creds_path}"
            )

    # Load credentials
    try:
        with open(creds_path, 'r') as file:
            lines = file.read().strip().splitlines()

        if len(lines) < 2:
            raise ValueError(
                "Credentials file must contain at least 2 lines: username and password"
            )

        username = lines[0].strip()
        password = lines[1].strip()

        if not username or not password:
            raise ValueError(
                "Username and password cannot be empty"
            )

        return username, password

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error reading credentials: {e}")


def validate_credentials(username, password):
    """
    Basic validation of credentials.
    Returns True if valid, False otherwise.
    """
    return bool(username and password and isinstance(username, str) and isinstance(password, str))


if __name__ == "__main__":
    # Quick test - create template if needed and show path
    if not credentials_exist():
        print("Creating credentials template...")
        create_credentials_template()
    else:
        print(f"Credentials file exists at: {get_credentials_path()}")
        try:
            username, password = load_credentials(create_if_missing=False)
            print(f"Successfully loaded credentials for user: {username}")
        except Exception as e:
            print(f"Could not load credentials: {e}")
