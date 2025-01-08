from telegram import Update
from telegram.ext import ContextTypes
import asyncio
from datetime import datetime
import os

class BroadcastHandler:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        if not await self._is_admin(update.effective_user.id):
            await update.message.reply_text("You don't have permission to use this command!")
            return

        # Get broadcast message
        broadcast_msg = ""
        
        # Check if command is replying to a message
        if update.message.reply_to_message:
            broadcast_msg = update.message.reply_to_message.text or update.message.reply_to_message.caption
            
            # If replying to media with caption
            if not broadcast_msg and update.message.reply_to_message.caption:
                broadcast_msg = update.message.reply_to_message.caption
                
        # If not replying, check command arguments
        elif context.args:
            broadcast_msg = ' '.join(context.args)
        
        # If no message found
        if not broadcast_msg:
            await update.message.reply_text(
                "Please either:\n"
                "1. Reply to a message with /broadcast\n"
                "2. Use /broadcast with your message\n\n"
                "Example: /broadcast Hello everyone!"
            )
            return

        status_msg = await update.message.reply_text("Broadcasting message...")
        
        # Get all users
        users = list(self.users_collection.find({}))
        total_users = self.users_collection.count_documents({})
        successful = 0
        failed = 0

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=broadcast_msg,
                    parse_mode='HTML'
                )
                successful += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                failed += 1
                if "blocked" in str(e).lower():
                    self.users_collection.update_one(
                        {"user_id": user['user_id']},
                        {"$set": {"blocked": True}}
                    )

            if (successful + failed) % 25 == 0:
                await status_msg.edit_text(
                    f"Broadcasting...\n"
                    f"Progress: {successful + failed}/{total_users}\n"
                    f"Success: {successful}\n"
                    f"Failed: {failed}"
                )

        await status_msg.edit_text(
            f"✅ Broadcast completed!\n\n"
            f"Total users: {total_users}\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}"
        )

    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin or sudo user"""
        # Get admin ID from env
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        
        # Get sudo users from env
        sudo_users = os.getenv('SUDO_USERS', '')
        sudo_list = [int(id.strip()) for id in sudo_users.split(',') if id.strip()]
        
        return user_id == admin_id or user_id in sudo_list 