#!/usr/bin/env python3
"""
Central update script for CustomTools.
Manages updates for all tools in the CustomTools repository.
Can be called from individual tools or run standalone.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import zipfile
import shutil
import tempfile
from pathlib import Path


def find_customtools_root():
    """
    Find the CustomTools root directory.
    Works whether called from root or from a subfolder.
    """
    current_dir = Path.cwd()

    # Check if current directory has versions.json (we're in root)
    if (current_dir / "versions.json").exists():
        return current_dir

    # Check parent directory (we're in a subfolder like FDBSearching - active)
    if (current_dir.parent / "versions.json").exists():
        return current_dir.parent

    # If neither works, assume current directory is root
    print("Warning: Could not find CustomTools root. Assuming current directory.")
    return current_dir


def get_versions_cache_path(customtools_root):
    """Get path to the cached versions file."""
    return os.path.join(customtools_root, ".versions_cache.json")


def load_versions_cache(cache_path):
    """Load cached versions and check if it's still fresh (less than 24 hours old)."""
    try:
        if not os.path.exists(cache_path):
            return None

        with open(cache_path, 'r') as f:
            cache_data = json.load(f)

        timestamp = cache_data.get('timestamp', 0)
        current_time = time.time()
        hours_old = (current_time - timestamp) / 3600

        # Return cache if less than 24 hours old
        if hours_old < 24:
            return cache_data.get('versions')

        return None  # Cache is stale
    except Exception as e:
        return None


def save_versions_cache(cache_path, versions_data):
    """Save versions data with timestamp to cache."""
    try:
        cache_data = {
            'timestamp': time.time(),
            'versions': versions_data
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        pass  # Silently fail on cache save


def download_versions_json():
    """
    Download only the versions.json file from the repository.
    Returns the parsed JSON data or None on failure.
    """
    url = "https://raw.githubusercontent.com/Payhn/CustomTools/main/versions.json"

    try:
        print("Checking for updates...")
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.URLError as e:
        print(f"Error checking for updates: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during version check: {e}")
        return None


def load_versions(versions_file):
    """Load versions from a versions.json file."""
    try:
        with open(versions_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading versions file: {e}")
        return {"tools": {}}


def save_versions(versions_file, versions_data):
    """Save versions to a versions.json file."""
    try:
        with open(versions_file, 'w') as f:
            json.dump(versions_data, f, indent=2)
    except Exception as e:
        print(f"Error saving versions file: {e}")


def download_repo_zip(temp_dir):
    """
    Download the CustomTools repo as a zip file.
    Returns path to the downloaded zip file.
    """
    url = "https://github.com/Payhn/CustomTools/archive/refs/heads/main.zip"
    zip_path = os.path.join(temp_dir, "CustomTools.zip")

    try:
        print("Downloading latest CustomTools repository...")
        urllib.request.urlretrieve(url, zip_path)
        return zip_path
    except urllib.error.URLError as e:
        print(f"Error downloading repository: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during download: {e}")
        return None


def extract_zip(zip_path, extract_dir):
    """Extract the zip file and return path to the extracted CustomTools folder."""
    try:
        print("Extracting repository...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # The zip contains CustomTools-main/ folder
        extracted_root = os.path.join(extract_dir, "CustomTools-main")
        if os.path.exists(extracted_root):
            return extracted_root
        else:
            print("Error: Could not find CustomTools-main folder in extracted zip")
            return None
    except Exception as e:
        print(f"Error extracting zip: {e}")
        return None


def compare_versions(local_versions, remote_versions):
    """
    Compare local and remote versions.
    Returns dict with tools that need updates.
    Format: {"tool_name": {"current": "1.0.0", "latest": "1.0.1"}}
    """
    updates_available = {}

    local_tools = local_versions.get("tools", {})
    remote_tools = remote_versions.get("tools", {})

    for tool_name, remote_version in remote_tools.items():
        local_version = local_tools.get(tool_name, "0.0.0")

        if is_newer_version(local_version, remote_version):
            updates_available[tool_name] = {
                "current": local_version,
                "latest": remote_version
            }

    return updates_available


def is_newer_version(current, latest):
    """Compare versions. Returns True if latest > current."""
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]

        # Pad with zeros if different lengths
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))

        return latest_parts > current_parts
    except:
        return False


def display_update_options(updates_available, all_tools):
    """Display available updates and get user selection."""
    print("\n" + "="*60)
    print("Update Status")
    print("="*60)

    if not updates_available and not all_tools:
        print("No tools found.")
        return []

    tool_list = []

    # Show tools with updates
    for i, tool_name in enumerate(all_tools, 1):
        if tool_name in updates_available:
            update_info = updates_available[tool_name]
            print(f"[{i}] {tool_name}")
            print(f"    {update_info['current']} → {update_info['latest']}")
            tool_list.append(tool_name)
        else:
            print(f"[{i}] {tool_name} (up to date)")
            tool_list.append(tool_name)

    print("="*60)

    if not updates_available:
        print("All tools are up to date!")
        return []

    # Get user selection
    while True:
        user_input = input("\nSelect tools to update (e.g., '1,2' or 'all' or 'none'): ").strip().lower()

        if user_input == "none":
            return []

        if user_input == "all":
            return [tool for tool in all_tools if tool in updates_available]

        try:
            selections = [int(x.strip()) - 1 for x in user_input.split(',')]
            selected_tools = []
            for idx in selections:
                if 0 <= idx < len(tool_list):
                    tool = tool_list[idx]
                    if tool in updates_available:
                        selected_tools.append(tool)

            if selected_tools:
                return selected_tools
            else:
                print("No valid updates selected. Please try again.")
        except:
            print("Invalid input. Please enter numbers separated by commas, 'all', or 'none'.")


def copy_tool_folder(source_path, dest_path):
    """Copy an entire tool folder from source to destination."""
    try:
        # Remove existing folder if it exists
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)

        # Copy the new folder
        shutil.copytree(source_path, dest_path)
        return True
    except Exception as e:
        print(f"Error copying {os.path.basename(dest_path)}: {e}")
        return False


def update_tools(customtools_root, extracted_repo, selected_tools, remote_versions):
    """Update selected tools by copying from extracted repo."""
    success_count = 0

    print("\n" + "="*60)
    print("Installing Updates")
    print("="*60)

    for tool_name in selected_tools:
        source_path = os.path.join(extracted_repo, tool_name)
        dest_path = os.path.join(customtools_root, tool_name)

        if not os.path.exists(source_path):
            print(f"✗ {tool_name}: Source not found in repository")
            continue

        print(f"Updating {tool_name}...", end=" ")
        if copy_tool_folder(source_path, dest_path):
            print("✓")
            success_count += 1
        else:
            print("✗")

    print("="*60)

    # Update versions.json
    if success_count > 0:
        local_versions = load_versions(os.path.join(customtools_root, "versions.json"))

        for tool_name in selected_tools:
            if tool_name in remote_versions.get("tools", {}):
                local_versions["tools"][tool_name] = remote_versions["tools"][tool_name]

        save_versions(os.path.join(customtools_root, "versions.json"), local_versions)
        print(f"\n✓ Successfully updated {success_count} tool(s)!")
    else:
        print("\n✗ No tools were updated.")

    return success_count > 0


def main(check_only=False):
    """
    Main update function.
    If check_only=True, only check for updates without prompting to install.
    """
    customtools_root = find_customtools_root()
    cache_path = get_versions_cache_path(customtools_root)

    # Load local versions
    local_versions = load_versions(os.path.join(customtools_root, "versions.json"))

    # For check_only mode, try to use cached versions first
    if check_only:
        remote_versions = load_versions_cache(cache_path)

        if not remote_versions:
            # Cache is stale or doesn't exist, download fresh versions
            remote_versions = download_versions_json()
            if remote_versions:
                save_versions_cache(cache_path, remote_versions)

        if not remote_versions:
            return False

        # Display status
        print("\n" + "="*60)
        print("CustomTools Update Check")
        print("="*60)

        updates_available = compare_versions(local_versions, remote_versions)
        all_tools = sorted(remote_versions.get("tools", {}).keys())

        for tool_name in all_tools:
            local_version = local_versions.get("tools", {}).get(tool_name, "0.0.0")
            remote_version = remote_versions.get("tools", {}).get(tool_name, "?")

            if tool_name in updates_available:
                print(f"{tool_name}: {local_version} → {remote_version} [UPDATE]")
            else:
                print(f"{tool_name}: {remote_version} (up to date)")
        print("="*60)
        return len(updates_available) > 0

    # For actual updates, download full repo
    temp_dir = tempfile.mkdtemp()

    try:
        # Download and extract repo
        zip_path = download_repo_zip(temp_dir)
        if not zip_path:
            return False

        extracted_repo = extract_zip(zip_path, temp_dir)
        if not extracted_repo:
            return False

        # Load remote versions
        remote_versions_file = os.path.join(extracted_repo, "versions.json")
        remote_versions = load_versions(remote_versions_file)

        # Update cache with fresh versions
        save_versions_cache(cache_path, remote_versions)

        # Compare versions
        updates_available = compare_versions(local_versions, remote_versions)
        all_tools = sorted(remote_versions.get("tools", {}).keys())

        # Get user selection
        selected_tools = display_update_options(updates_available, all_tools)

        if not selected_tools:
            if updates_available:
                print("No tools selected for update.")
            return False

        # Perform updates
        return update_tools(customtools_root, extracted_repo, selected_tools, remote_versions)

    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


if __name__ == "__main__":
    # Support --check-only flag to just show update status
    check_only = "--check-only" in sys.argv

    try:
        success = main(check_only=check_only)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ An unexpected error occurred: {e}")
        sys.exit(1)
