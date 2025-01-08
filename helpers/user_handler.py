from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import os

class UserHandler:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']

    async def handle_new_user(self, user_id: int, username: str = None):
        """Add new user to database if not exists"""
        if not self.users_collection.find_one({"user_id": user_id}):
            self.users_collection.insert_one({
                "user_id": user_id,
                "username": username,
                "joined_at": datetime.now()
            })

    async def get_users_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command"""
        if not await self._is_admin(update.effective_user.id):
            await update.message.reply_text("You don't have permission to use this command!")
            return

        total_users = self.users_collection.count_documents({})
        active_users = self.users_collection.count_documents({"blocked": {"$ne": True}})
        
        stats = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"Total Users: {total_users}\n"
            f"Active Users: {active_users}\n"
            f"Blocked Users: {total_users - active_users}"
        )
        
        await update.message.reply_text(stats, parse_mode='HTML')

    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin or sudo user"""
        # Get admin ID from env
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        
        # Get sudo users from env
        sudo_users = os.getenv('SUDO_USERS', '')
        sudo_list = [int(id.strip()) for id in sudo_users.split(',') if id.strip()]
        
        return user_id == admin_id or user_id in sudo_list 