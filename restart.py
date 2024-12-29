import os
import sys
import subprocess

def restart():
    """Restart the bot."""
    try:
        # Get the current Python executable and main script path
        python = sys.executable
        script = os.path.abspath('main.py')

        # Execute the main script again
        subprocess.Popen([python, script])
        os._exit(0)
    except Exception as e:
        print(f"Failed to restart: {e}")
