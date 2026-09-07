#!/bin/bash
# Stop and remove the hourly job on THIS Mac. Leaves the code + repo alone.
PLIST="$HOME/Library/LaunchAgents/com.campus.schedule.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Hourly job removed from this Mac. (Folder and GitHub repo untouched.)"
