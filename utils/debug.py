import os
import sys
import time
from datetime import datetime

level = 3
log_file = "game_debug.log"

def clear_log():
    """Clear the log file when starting a new game session"""
    with open(log_file, 'w') as f:
        f.write(f"=== New Game Session Started at {datetime.now()} ===\n")

def out(output, debug_level=1):
    """Write debug output to file if debug_level meets or exceeds the threshold"""
    if debug_level >= level:  # Note: Changed to <= for more intuitive level handling
        print(output)
        try:
            with open(log_file, 'a') as f:
                f.write(f"{output}\n")
        except Exception as e:
            print(f"Error writing to debug log: {e}")

# Clear the log when this module is imported
clear_log()
