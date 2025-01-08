from telegram import Update
from telegram.ext import ContextTypes
import re

class BatchCaptionHandler:
    def __init__(self, config):
        self.config = config
        
    async def handle_bsetcaption_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bsetcaption command for batch caption prefix update"""
        try:
            # Check if there are arguments
            if not context.args:
                await update.message.reply_text(
                    "❌ Correct Format:\n"
                    "/bsetcaption <batch_link> -add <prefix_text>\n\n"
                    "Example:\n"
                    "/bsetcaption https://example.com/batch_123456 -add Drama Name S01"
                )
                return

            text = ' '.join(context.args)
            
            # Extract batch link and prefix text
            match = re.match(r'(https?://[^\s]+/batch_\w+)\s+-add\s+(.+)', text)
            if not match:
                await update.message.reply_text(
                    "❌ Invalid format! Please use:\n"
                    "/bsetcaption <batch_link> -add <prefix_text>"
                )
                return

            batch_link = match.group(1)
            prefix_text = match.group(2).strip()
            
            # Extract batch code from link
            batch_code = batch_link.split('batch_')[-1]
            
            # Get the database from config
            db = self.config.db
            files_collection = db['files']
            batches_collection = db['batches']
            
            # Find the batch
            batch = batches_collection.find_one({"batch_code": batch_code})
            if not batch:
                await update.message.reply_text("❌ Batch not found!")
                return
            
            # Get files from batch
            batch_files = batch.get('files', [])
            if not batch_files:
                await update.message.reply_text(
                    f"❌ No files found in batch {batch_code}!"
                )
                return
            
            # Update counter
            updated_count = 0
            updated_batch_files = []
            
            # Update each file's caption
            for file_info in batch_files:
                file_id = file_info.get('file_id')
                original_caption = file_info.get('caption', '')
                
                # Add space after prefix if there's a caption
                new_caption = f"{prefix_text} {original_caption}" if original_caption else prefix_text
                
                # Update in files collection
                files_collection.update_one(
                    {"file_id": file_id},
                    {"$set": {"caption": new_caption}}
                )
                
                # Update file info for batch document
                file_info['caption'] = new_caption
                updated_batch_files.append(file_info)
                updated_count += 1
            
            # Update the batch document with new captions
            batches_collection.update_one(
                {"batch_code": batch_code},
                {"$set": {"files": updated_batch_files}}
            )
            
            await update.message.reply_text(
                f"✅ Successfully updated captions for {updated_count} files!\n\n"
                f"Added prefix: {prefix_text}\n"
                f"Batch code: {batch_code}"
            )

        except Exception as e:
            print(f"Error updating batch captions: {str(e)}")
            await update.message.reply_text("❌ An error occurred while updating batch captions.") 