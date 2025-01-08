from telegram import Update
from telegram.ext import ContextTypes
import re
import os

class BatchUpdateHandler:
    def __init__(self, config):
        self.config = config
        self.db = config.db
        self.files_collection = self.db['files']
        self.batches_collection = self.db['batches']
        self.waiting_for_files = {}  # Store user states
        
    def extract_batch_code(self, text: str) -> str:
        """Extract batch code from different formats of links/text"""
        # Try to extract from direct worker URL
        worker_url = os.getenv('WORKER_URL', '').rstrip('/')
        if text.startswith(worker_url):
            match = re.search(r'batch_(\d+)', text)
            if match:
                return match.group(1)
                
        # Try to extract from telegram bot link
        if 'start=batch_' in text:
            match = re.search(r'start=batch_(\d+)', text)
            if match:
                return match.group(1)
                
        # Try direct batch code
        if text.startswith('batch_'):
            return text[6:]
            
        # Try just the number
        if text.isdigit():
            return text
            
        return None
        
    async def handle_batch_update_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /batch command with existing batch link"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide batch link and number of files!\n\n"
                "<b>Examples:</b>\n"
                "1. /batch https://tele.k-drama.workers.dev/batch_12345 2\n"
                "2. /batch https://t.me/autoforwardbd_bot?start=batch_12345 3\n"
                "3. /batch batch_12345 2\n"
                "4. /batch 12345 2",
                parse_mode='HTML'
            )
            return
            
        batch_link = context.args[0]
        try:
            num_files = int(context.args[1])
            if num_files < 1:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid number of files!")
            return
            
        # Extract batch code
        batch_code = self.extract_batch_code(batch_link)
        if not batch_code:
            await update.message.reply_text(
                "❌ Invalid batch link format!\n\n"
                "Please use one of these formats:\n"
                "1. https://tele.k-drama.workers.dev/batch_12345\n"
                "2. https://t.me/autoforwardbd_bot?start=batch_12345\n"
                "3. batch_12345\n"
                "4. 12345"
            )
            return
            
        # Check if batch exists
        batch = self.batches_collection.find_one({"batch_code": batch_code})
        if not batch:
            await update.message.reply_text("❌ Batch not found!")
            return
            
        # Store user state
        user_id = update.effective_user.id
        self.waiting_for_files[user_id] = {
            "batch_code": batch_code,
            "files_needed": num_files,
            "files_added": 0,
            "new_files": []
        }
        
        await update.message.reply_text(
            f"✅ Ready to update batch!\n\n"
            f"Please send {num_files} file{'s' if num_files > 1 else ''} to add to the batch.\n"
            f"Progress: 0/{num_files} files added"
        )
        
    async def handle_update_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handle files for batch update. Returns True if handled, False otherwise."""
        user_id = update.effective_user.id
        user_state = self.waiting_for_files.get(user_id)
        
        if not user_state:
            return False
            
        message = update.message
        file_id = None
        file_type = None
        
        # Get file info
        if message.document:
            file_id = message.document.file_id
            file_type = "document"
            file_name = message.document.file_name
            mime_type = message.document.mime_type
            file_size = message.document.file_size
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
            file_name = message.video.file_name
            mime_type = message.video.mime_type
            file_size = message.video.file_size
        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audio"
            file_name = message.audio.file_name
            mime_type = message.audio.mime_type
            file_size = message.audio.file_size
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
            file_name = None
            mime_type = None
            file_size = message.photo[-1].file_size
            
        if not file_id:
            await message.reply_text("❌ Please send a valid file (document/video/audio/photo)!")
            return True
            
        # Create file document
        file_doc = {
            "file_id": file_id,
            "file_type": file_type,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "caption": message.caption,
            "user_id": user_id
        }
        
        # Add to user state
        user_state["files_added"] += 1
        user_state["new_files"].append(file_doc)
        
        # Update progress
        await message.reply_text(
            f"✅ File {user_state['files_added']}/{user_state['files_needed']} added!\n"
            f"Progress: {user_state['files_added']}/{user_state['files_needed']} files"
        )
        
        # Check if all files received
        if user_state["files_added"] >= user_state["files_needed"]:
            # Update batch in database
            batch_code = user_state["batch_code"]
            batch = self.batches_collection.find_one({"batch_code": batch_code})
            
            if not batch:
                await message.reply_text("❌ Error: Batch not found!")
                del self.waiting_for_files[user_id]
                return True
                
            # Add new files to batch
            if "files" not in batch:
                batch["files"] = []
            batch["files"].extend(user_state["new_files"])
            
            # Update batch in database
            self.batches_collection.update_one(
                {"batch_code": batch_code},
                {"$set": {"files": batch["files"]}}
            )
            
            # Generate batch link
            worker_url = os.getenv('WORKER_URL', '').rstrip('/')
            batch_link = f"{worker_url}/batch_{batch_code}"
            
            # Send completion message
            await message.reply_text(
                f"✅ Batch updated successfully!\n\n"
                f"Added {user_state['files_added']} new file(s)\n"
                f"Total files in batch: {len(batch['files'])}\n"
                f"Batch link: {batch_link}"
            )
            
            # Clear user state
            del self.waiting_for_files[user_id]
            
        return True 