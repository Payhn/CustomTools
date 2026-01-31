# CustomTools Setup Guide

## First Time Setup

### Step 1: Install Dependencies

If you haven't already, install the required Python package:

```bash
pip install paramiko
```

### Step 2: Run the Program

From the CustomTools directory, run:

```bash
python3 main.py
```

Or make it executable and run directly:

```bash
chmod +x main.py
./main.py
```

### Step 3: Set Up Credentials

On first run, the program will:
1. Check for `credentials.txt`
2. If it doesn't exist, create a template with placeholders
3. Display a message asking you to edit the file

The program will exit and ask you to fill in your credentials.

### Step 4: Edit Your Credentials

Open `credentials.txt` in your editor:

```bash
nano credentials.txt
```

Replace the placeholders:
- Line 1: Your SSH username
- Line 2: Your SSH password

Example:
```
admin
mySecurePassword123
```

**Important**: Keep this file secure! Consider restricting permissions:

```bash
chmod 600 credentials.txt
```

### Step 5: Run Again

Now run the program again:

```bash
python3 main.py
```

You should see the main menu!

## Using the Program

### Main Menu Navigation

After starting the program, you'll see:

```
============================================================
CustomTools v1.0.0 - Main Menu [0 active]
============================================================

Available Tools:
  1. FDB Searching    - Search for MAC addresses on switches
  2. Create Backup    - Backup switch configurations
  3. Bulk Update      - Run commands on multiple switches
  4. Self Lookup      - Find your device on the network

Connection Management:
  5. Interactive Session   - Direct access to a switch
  6. List Connections      - Show active connections
  7. Close Connection      - Disconnect from a switch

Program Control:
  8. Exit - Close all connections and exit
============================================================

Select option (1-8):
```

### Example Workflow

1. **Run FDB Search** - Select option `1`
2. **Search for a MAC address** - Enter MAC and switch IP
3. **Return to main menu** - After search completes
4. **Interactive session** - Select option `5` and connect to a switch
5. **Run commands** - Execute arbitrary switch commands
6. **Type `exit`** to close interactive session
7. **Return to main menu** - Back to the menu automatically
8. **Close connection** - Select option `7` if you want to disconnect
9. **Exit program** - Select option `8` to cleanly shutdown

## Troubleshooting

### "Credentials file not found"

The program tried to create `credentials.txt` but couldn't. Check:
1. Do you have write permissions in the CustomTools directory?
2. Is the directory readable?

### "Failed to connect to [hostname]"

Check:
1. Are your credentials correct?
2. Can you ping the switch?
3. Does the SSH service respond on port 22?
4. Are you using the correct IP address?

### "FDBSearching module not found"

Make sure you're running from the CustomTools root directory.

### Import errors

Make sure paramiko is installed:

```bash
pip install paramiko
```

## Connection Persistence

One of the key features is that SSH connections persist. This means:

- Connect to switch 10.10.1.1 in FDB search tool
- Return to main menu
- Connect to interactive session on 10.10.1.1
- **Same connection is reused** - no new login needed

This saves time and keeps your workflow smooth.

## Security Notes

1. **Credentials file** - Keep `credentials.txt` private:
   ```bash
   chmod 600 credentials.txt
   ```

2. **SSH keys** - For production, consider using SSH keys instead of passwords

3. **Connection cleanup** - When you exit (option 8), all connections are cleanly closed

## Next Steps

Once you're comfortable with the main workflow, check out:

- **FDBSearching/main.py** - Original implementation (still usable standalone)
- **CreateBackup/**, **BulkUpdate/**, **SelfLookup/** - These tools are planned for integration

## Need Help?

- Check that Python 3.6+ is installed: `python3 --version`
- Verify paramiko is installed: `python3 -c "import paramiko; print('OK')"`
- Test SSH connection manually: `ssh username@switchip`
- Check the main README.md for architecture details
