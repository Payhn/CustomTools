# BulkCommands Tool

Execute a list of commands on multiple network switches with comprehensive logging.

## Features

- ✓ Run multiple commands sequentially on each switch
- ✓ CSV-driven configuration (switches and commands)
- ✓ Comprehensive session-based logging with timestamps
- ✓ Per-device organized log files
- ✓ Connection pooling and reuse
- ✓ Automatic error recovery (continue on failure)
- ✓ Works in standalone mode or integrated with central menu
- ✓ Full audit trail of all command output

## Quick Start

### Using the Central Menu (Recommended)

1. Run the main menu: `python main.py` (from CustomTools directory)
2. Select option 3: "Bulk Update"
3. Edit `BulkCommands/switches.csv` and `BulkCommands/commands.csv`
4. Run the tool again
5. Check `BulkCommands/Logs/` for output

### Using Standalone Mode

1. Double-click `start.bat` in the BulkCommands directory
2. Edit CSV files when prompted
3. Run again with your switches and commands

## CSV File Format

### switches.csv

A CSV file containing a list of switch hostnames or IP addresses:

```csv
hostname
10.10.1.1
10.10.1.2
switch-core-01
```

**Requirements:**
- First row must be the header: `hostname`
- One switch per row
- Can use IP addresses or hostnames
- Empty rows are automatically skipped

### commands.csv

A CSV file containing a list of commands to execute:

```csv
command
show version
show system
show fdb
```

**Requirements:**
- First row must be the header: `command`
- One command per row
- Commands execute in the order listed
- Empty rows are automatically skipped

**Example commands** (for Ethernet switches):
```csv
command
show version
show system
show vlan
show fdb
show ports information
show lldp neighbors
```

## Log Files

Logs are organized by device and session:

```
BulkCommands/Logs/
├── 10.10.1.1/
│   ├── 20260211_143022.txt     (First session)
│   ├── 20260211_143522.txt     (Second session)
│   └── ...
├── 10.10.1.2/
│   ├── 20260211_143045.txt
│   └── ...
└── switch-core-01/
    ├── 20260211_143100.txt
    └── ...
```

### Log File Format

Each timestamped log file contains a session header, command outputs, and a summary footer:

```
================================================================================
BulkCommands Session Log
Switch: 10.10.1.1
Session Start: 2026-02-11 14:30:22
================================================================================

[14:30:25] Executing: show version
--------------------------------------------------------------------------------
<command output here>
--------------------------------------------------------------------------------
Execution Time: 1.23s
Status: Success

[14:30:27] Executing: show system
--------------------------------------------------------------------------------
<command output here>
--------------------------------------------------------------------------------
Execution Time: 0.87s
Status: Success

================================================================================
Session End: 2026-02-11 14:30:45
Total Commands: 3 | Successful: 2 | Errors: 1
================================================================================
```

## Usage Workflow

### First Time Setup

1. Run the tool
2. Template CSV files will be auto-created: `switches.csv` and `commands.csv`
3. Edit `switches.csv` and add your switch IP addresses/hostnames
4. Edit `commands.csv` and add the commands you want to execute
5. Run the tool again

### Running Commands

1. Start the tool (via menu or start.bat)
2. Tool loads your switches and commands from CSV
3. For each switch:
   - Connects via SSH
   - Runs all commands sequentially
   - Logs all output with timestamps
   - Continues to next switch if any errors occur
4. View results in `BulkCommands/Logs/[switch]/[timestamp].txt`

### Running Again Later

1. If you run the tool again, a NEW timestamped log file is created for each switch
2. Old log files are preserved
3. All output is appended to the new session file
4. This creates an audit trail of all executions

## Error Handling

The tool is designed to maximize work completed despite errors:

- **Connection fails to a switch**: That switch is skipped, tool continues with next switch
- **Command fails on a switch**: Error is logged, tool continues with next command
- **Timeout on command**: Timeout is logged, tool continues
- **CSV file issues**: Tool exits gracefully with error message

All errors are logged to the session file for review.

## Console Output

The tool displays progress as it runs:

```
[1/5] Processing: 10.10.1.1
  [1/3] show version... ✓
  [2/3] show system... ✓
  [3/3] show fdb... ⚠️

[2/5] Processing: 10.10.1.2
  ✗ Connection failed: Connection refused
```

After completion, a summary is shown:

```
================================================================================
BulkCommands Execution Summary
================================================================================
Switches Processed: 4/5
Connection Failures: 1
Total Commands Executed: 12
  ✓ Successful: 11
  ✗ Errors: 1
📁 Logs Location: G:\...\BulkCommands\Logs
================================================================================
```

## Troubleshooting

### CSV Templates Not Created

If template files don't appear, check:
- File permissions in the BulkCommands directory
- Windows firewall or antivirus blocking file creation
- Disk space availability

### Connection Timeouts

- Verify switch IP addresses are correct
- Check network connectivity to switches
- Increase timeout (edit main.py, default is 30 seconds)
- Try with a single switch first

### No Output in Log Files

- Verify commands are valid for your switch type
- Check that you have proper permissions on the switch
- Try commands manually via SSH first
- Check for special characters in command output

### Logs Directory Not Found

- The Logs directory is auto-created when the tool runs
- Verify you have write permissions in the BulkCommands directory
- Try running with administrator privileges

## Advanced

### Changing Command Timeout

Edit `main.py` line 249 (in `execute_command` function):
```python
stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
```

Change `30` to your desired timeout in seconds.

### Customizing Log Timestamp Format

Edit `main.py` line 130 (in `get_log_file_path` function):
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

Reference: [Python strftime format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)

### Using Hostnames Instead of IPs

Simply put hostnames in `switches.csv` instead of IP addresses:

```csv
hostname
switch-core-01
switch-dist-02
switch-access-03
```

The tool will resolve them automatically.

## Examples

### Example 1: Backup Running Config

**switches.csv:**
```csv
hostname
10.10.1.1
10.10.1.2
```

**commands.csv:**
```csv
command
show running-config
```

Then review the output in `Logs/10.10.1.1/` and `Logs/10.10.1.2/`

### Example 2: Network Inventory Collection

**switches.csv:**
```csv
hostname
switch-core-01
switch-dist-01
switch-dist-02
switch-access-01
switch-access-02
```

**commands.csv:**
```csv
command
show version
show system
show lldp neighbors
```

This creates comprehensive documentation of your network.

### Example 3: Monitoring and Verification

**switches.csv:**
```csv
hostname
10.10.1.1
```

**commands.csv:**
```csv
command
show vlan
show ports information
show port-security
show system temperature
```

Run this periodically to monitor switch health.

## Integration with Central Menu

When you run this tool from the CustomTools central menu:
- SSH connections are shared across tools
- Return to main menu when done
- Session state is preserved

## Technical Details

### Standalone Mode

- Creates local SSH connections for each switch
- Credentials loaded from `credentials.txt`
- Closes all connections on exit
- Best for running just this tool

### Integrated Mode

- Uses shared ConnectionManager from main.py
- Reuses SSH connections across tools
- Returns control to main menu
- Best for multi-tool workflows

### File Structure

```
BulkCommands/
├── main.py           # Core implementation (both modes)
├── integrated.py     # Integration wrapper for central menu
├── start.bat         # Standalone launcher
├── readme.md         # This file
├── switches.csv      # Your switch list (auto-created)
├── commands.csv      # Your command list (auto-created)
└── Logs/             # Output logs (auto-created)
```

## Support

For issues or questions:
1. Check this readme for troubleshooting
2. Review your CSV file formatting
3. Try with a test command first (e.g., `show version`)
4. Check log files for detailed error messages
