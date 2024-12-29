from typing import List
from telegram import Update
from telegram.ext import ContextTypes
from .auto_delete_handler import AutoDeleteHandler
import os
from .shortener import Shortener

class BatchHandler:
    def __init__(self, db, config):
        self.db = db
        self.user_files = {}  # Store temporary files for batch processing
        self.auto_delete = AutoDeleteHandler()
        self.shortener = Shortener(config)
        
    async def handle_batch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /batch command"""
        try:
            # Get requested file count
            if not context.args:
                await update.message.reply_text("Please specify how many files you want to batch.\nExample: /batch 4")
                return
                
            count = int(context.args[0])
            if count < 1 or count > 32:
                await update.message.reply_text("Please specify a number between 1 and 32.")
                return
                
            # Store user's batch request
            user_id = update.effective_user.id
            self.user_files[user_id] = {
                'requested_count': count,
                'files': [],
                'message_id': update.message.message_id
            }
            
            await update.message.reply_text(
                f"Please send {count} files one by one.\n"
                f"Files received: 0/{count}"
            )
            
        except ValueError:
            await update.message.reply_text("Please provide a valid number.\nExample: /batch 4")
    
    async def handle_batch_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle files for batch processing"""
        user_id = update.effective_user.id
        if user_id not in self.user_files:
            return False
            
        batch_info = self.user_files[user_id]
        if len(batch_info['files']) >= batch_info['requested_count']:
            return False
            
        # Add file to batch
        file_info = self._get_file_info(update.message)
        if file_info:
            batch_info['files'].append(file_info)
            
            # Update progress
            files_received = len(batch_info['files'])
            total_files = batch_info['requested_count']
            
            await update.message.reply_text(
                f"File {files_received} of {total_files} received.\n"
                f"{'Batch complete!' if files_received == total_files else f'Send {total_files - files_received} more files.'}"
            )
            
            # If batch is complete, create batch link
            if files_received == total_files:
                await self._create_batch_link(update, context, batch_info['files'])
                del self.user_files[user_id]
                
            return True
            
        return False
    
    def _get_file_info(self, message):
        """Extract file information from message"""
        if message.document:
            return {'file': message.document, 'type': 'document'}
        elif message.video:
            return {'file': message.video, 'type': 'video'}
        elif message.audio:
            return {'file': message.audio, 'type': 'audio'}
        elif message.photo:
            return {'file': message.photo[-1], 'type': 'photo'}
        return None
        
    async def _create_batch_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, files: List[dict]):
        """Create a shareable link for batch of files"""
        try:
            batch_code = str(abs(hash(str(files) + str(update.effective_user.id))))[:8]
            
            # Save batch info
            batch_data = {
                'batch_code': batch_code,
                'files': [
                    {
                        'file_id': f['file'].file_id,
                        'file_type': f['type'],
                        'file_name': getattr(f['file'], 'file_name', None),
                        'caption': update.message.caption or getattr(f['file'], 'file_name', None)
                    }
                    for f in files
                ],
                'user_id': update.effective_user.id
            }
            
            self.db['batches'].insert_one(batch_data)
            
            # Generate permanent link using worker URL
            worker_url = os.getenv('WORKER_URL', '').rstrip('/')
            share_link = f"{worker_url}/batch_{batch_code}"
            
            # Shorten the link if enabled
            shortened_link = await self.shortener.shorten_url(share_link)
            
            await update.message.reply_text(
                f"Here's your batch shareable link:\n{shortened_link}"
            )
            
        except Exception as e:
            print(f"Error creating batch link: {str(e)}")
            import traceback
            print(traceback.format_exc())
            await update.message.reply_text("Sorry, couldn't create batch link!")

    async def handle_batch_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, batch_doc):
        """Handle batch file sharing with auto-delete"""
        try:
            sent_messages = []
            
            # Add info message about auto-delete
            delete_time = int(os.getenv('AUTO_DELETE_TIME', '30'))
            info_msg = await update.message.reply_text(
                f"⚠️ These files will be automatically deleted after {delete_time} minute{'s' if delete_time != 1 else ''}!"
            )
            sent_messages.append(info_msg)
            
            for file_info in batch_doc['files']:
                try:
                    file_type = file_info.get('file_type', 'document')
                    caption = file_info.get('caption', '')
                    prefix_name = self.db['settings'].find_one({"name": "prefix"}).get('value', '@CinemazBD')
                    
                    # Format caption
                    if caption:
                        caption = f"{prefix_name} - {caption}"
                    else:
                        caption = f"{prefix_name}\n<b>Here's your file!</b>"
                    
                    # Make the whole caption bold
                    caption = f"<b>{caption}</b>"
                    
                    if file_type == 'photo':
                        sent_msg = await update.message.reply_photo(
                            photo=file_info['file_id'],
                            caption=caption,
                            parse_mode='HTML'
                        )
                    elif file_type == 'video':
                        sent_msg = await update.message.reply_video(
                            video=file_info['file_id'],
                            caption=caption,
                            parse_mode='HTML'
                        )
                    elif file_type == 'audio':
                        sent_msg = await update.message.reply_audio(
                            audio=file_info['file_id'],
                            caption=caption,
                            parse_mode='HTML'
                        )
                    else:
                        sent_msg = await update.message.reply_document(
                            document=file_info['file_id'],
                            caption=caption,
                            parse_mode='HTML'
                        )
                    
                    sent_messages.append(sent_msg)
                    
                except Exception as e:
                    print(f"Error sending batch file: {str(e)}")
                    continue
            
            # Schedule all messages for deletion
            if sent_messages:
                await self.auto_delete.handle_shared_files(sent_messages)
                    
        except Exception as e:
            print(f"Error processing batch: {str(e)}")
            await update.message.reply_text("Sorry, couldn't process the batch!") 