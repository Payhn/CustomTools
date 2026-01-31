# CustomTools

A centralized suite of network management tools for switch operations, backup management, and device discovery.

## Quick Start

### 1. Set up Credentials

When you first run the program, it will create a credentials template:

```bash
python3 main.py
```

This creates `credentials.txt` in the CustomTools root directory. Edit it with your SSH credentials:

```
yourusername
yourpassword
```

### 2. Run the Program

```bash
python3 main.py
```

This launches the main menu where you can:
- Run different tools
- Manage SSH connections
- Have interactive sessions with switches

## Main Menu Features

### Available Tools

1. **FDB Searching** - Search for MAC addresses on switches
   - Mode 1: Search by MAC address across switches
   - Mode 2: Search by switch port to identify devices
   - Maintains connection cache across queries

2. **Create Backup** - Backup switch configurations (in development)
   - Connect to multiple switches
   - Save configuration backups
   - Log device information

3. **Bulk Update** - Run commands on multiple switches (in development)
   - Execute commands on a list of switches
   - Save results and logs

4. **Self Lookup** - Find your device on the network (in development)
   - Scan local network interfaces
   - Search for devices on the network
   - Identify which switch a device is connected to

### Connection Management

- **Interactive Session** - Direct SSH access to any switch
  - Use cached connections or create new ones
  - Execute arbitrary commands
  - Type `exit` to return to main menu

- **List Connections** - View all active SSH connections

- **Close Connection** - Manually disconnect from a specific switch

- **Exit** - Cleanly close all connections and exit the program

## Key Design Features

### Central Connection Management

All tools share the same SSH connection pool. This means:
- Connections persist across tool executions
- No need to reconnect to the same switch when running multiple queries
- Automatic connection testing and cleanup

### Credential Management

- Credentials are loaded once at startup
- Centralized `credentials.py` module handles all auth
- Template is auto-created if credentials don't exist

### Return to Menu

After each tool execution, you return to the main menu automatically. You can:
- Run multiple tools in sequence
- Have interactive sessions with different switches
- Create backups, do searches, and return to menu without closing the program

## Architecture

### main.py

The central orchestrator containing:
- `ConnectionManager`: Manages SSH connection pool
- `ToolRunner`: Executes available tools
- `MainMenu`: Handles menu navigation and user input

### FDBSearching/integrated.py

FDB search functionality adapted for use with central `ConnectionManager`.

### credentials.py

Handles loading and validating SSH credentials from `credentials.txt`.

## Workflow Example

1. Start program: `python3 main.py`
2. Select "FDB Searching" (1)
3. Search for a MAC address or port
4. Return to main menu
5. Select "Interactive Session" (5)
6. Connect to the same switch (connection reused)
7. Run commands directly on the switch
8. Exit interactive session
9. Return to main menu
10. Select "Exit" (8) to close all connections and quit

## Requirements

- Python 3.6+
- paramiko (for SSH connections)
- CSV file support for camera database (optional, for FDB searching)

Install requirements:
```bash
pip install paramiko
```

## File Structure

```
CustomTools/
├── main.py                      # Main entry point
├── credentials.py               # Credential management
├── credentials.txt              # Your SSH credentials (create on first run)
├── FDBSearching/
│   ├── main.py                 # Original FDB search implementation
│   ├── integrated.py           # FDB search adapted for central manager
│   └── macdatabase.txt         # MAC address database
├── CreateBackup/               # Backup tool (in development)
├── BulkUpdate/                 # Bulk update tool (in development)
├── SelfLookup/                 # Device lookup tool (in development)
└── README.md                   # This file
```