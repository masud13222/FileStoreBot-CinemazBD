from telegram import Update
from telegram.ext import ContextTypes
import re
import os

class DeleteHandler:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.files_collection = db['files']
        self.batches_collection = db['batches']
    
    async def handle_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /del command"""
        if not await self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
            
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a link to delete.\n\n"
                "Example:\n"
                "/del https://t.me/botusername?start=12345678\n"
                "or\n"
                "/del https://example.com/12345678"
            )
            return
            
        link = context.args[0]
        
        # Extract file/batch code from link
        code = self._extract_code(link)
        if not code:
            await update.message.reply_text("❌ Invalid link format!")
            return
            
        try:
            if code.startswith('batch_'):
                # Delete batch
                batch_code = code[6:]  # Remove 'batch_' prefix
                batch = self.batches_collection.find_one({"batch_code": batch_code})
                
                if batch:
                    # Delete all files in the batch first
                    for file_info in batch['files']:
                        self.files_collection.delete_one({
                            "file_id": file_info['file_id']
                        })
                    
                    # Then delete the batch
                    self.batches_collection.delete_one({"batch_code": batch_code})
                    await update.message.reply_text("✅ Batch and all its files deleted successfully!")
                else:
                    await update.message.reply_text("❌ Batch not found!")
            else:
                # Delete single file
                result = self.files_collection.delete_one({"file_code": code})
                if result.deleted_count > 0:
                    await update.message.reply_text("✅ File deleted successfully!")
                else:
                    await update.message.reply_text("❌ File not found!")
                    
        except Exception as e:
            print(f"Error deleting: {str(e)}")
            await update.message.reply_text("❌ Error deleting file/batch!")
    
    def _extract_code(self, link: str) -> str:
        """Extract file/batch code from various link formats"""
        # Try bot link format
        bot_match = re.search(r'start=(batch_)?([a-zA-Z0-9]+)', link)
        if bot_match:
            prefix = bot_match.group(1) or ''
            return f"{prefix}{bot_match.group(2)}"
            
        # Try worker link format
        worker_match = re.search(r'/(batch_)?([a-zA-Z0-9]+)$', link)
        if worker_match:
            prefix = worker_match.group(1) or ''
            return f"{prefix}{worker_match.group(2)}"
            
        return None
    
    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        sudo_users = self.config.get('sudo_users', [])
        return user_id == admin_id or user_id in sudo_users 