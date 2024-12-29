from telegram import Update, Message
from telegram.ext import ContextTypes
import asyncio
import os
from datetime import datetime, timedelta

class AutoDeleteHandler:
    def __init__(self):
        # Get delete time from env (in minutes)
        self.delete_time = int(os.getenv('AUTO_DELETE_TIME', '30'))

    async def schedule_delete(self, message: Message):
        """Schedule a message for deletion"""
        if self.delete_time > 0:
            await asyncio.sleep(self.delete_time * 60)  # Convert minutes to seconds
            try:
                await message.delete()
            except Exception as e:
                print(f"Error deleting message: {str(e)}")

    async def handle_shared_files(self, sent_messages: list[Message]):
        """Handle auto deletion for shared files"""
        for message in sent_messages:
            asyncio.create_task(self.schedule_delete(message)) 