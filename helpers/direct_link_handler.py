from telegram import Update
from telegram.ext import ContextTypes
import re
import os
import time
import base64

class DirectLinkHandler:
    def __init__(self, config):
        self.config = config
        self.worker_url = os.getenv('WORKER_URL', '').rstrip('/')

    async def handle_direct_link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /gdirect command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a Google Drive link.")
            return

        drive_link = context.args[0]
        # Extract file ID from the link
        file_id = self._extract_file_id(drive_link)
        if not file_id:
            await update.message.reply_text("❌ Invalid Google Drive link.")
            return

        # Generate direct link with encoded driveId and timestamp
        timestamp = int(time.time() * 1000)  # Current time in milliseconds
        encoded_drive_id = base64.urlsafe_b64encode(file_id.encode()).decode().rstrip('=')
        encoded_timestamp = base64.urlsafe_b64encode(str(timestamp).encode()).decode().rstrip('=')
        direct_link = f"{self.worker_url}/gdirect/{encoded_drive_id}/{encoded_timestamp}"
        await update.message.reply_text(f"✅ Here is your direct link (valid for 6 hours):\n{direct_link}")

    def _extract_file_id(self, link):
        """Extract file ID from Google Drive link"""
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', link)
        return match.group(1) if match else None