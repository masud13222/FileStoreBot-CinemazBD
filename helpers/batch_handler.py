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
        self.auto_delete = AutoDeleteHandler(db)
        self.shortener = Shortener(config)
        self.config = config
        
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
        file_info = None
        if message.document:
            file_info = {'file': message.document, 'type': 'document'}
        elif message.video:
            file_info = {'file': message.video, 'type': 'video'}
        elif message.audio:
            file_info = {'file': message.audio, 'type': 'audio'}
        elif message.photo:
            file_info = {'file': message.photo[-1], 'type': 'photo'}
        
        if file_info:
            # Add file name or caption
            file_info['file_name'] = getattr(file_info['file'], 'file_name', None)
            caption = message.caption or file_info['file_name']
            
            # Remove configured names from caption before saving
            if caption:
                remove_names = self.config.get('remove_names', [])
                caption_lower = caption.lower()
                for name in remove_names:
                    if name.lower() in caption_lower:
                        caption = caption.replace(name, '').replace('  ', ' ').strip()
                        caption_lower = caption.lower()
            
            file_info['caption'] = caption
        
        return file_info
        
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
                        'file_name': f['file_name'],
                        'caption': f['caption']
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
            
            # Prepare file names or captions
            file_details = "\n".join(
                f"{i+1}. {f['caption'] or f['file_name'] or 'No Name'}"
                for i, f in enumerate(batch_data['files'])
            )
            
            await update.message.reply_text(
                f"Here's your batch shareable link:\n{shortened_link}\n\nFiles:\n{file_details}"
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
            
            # Fetch auto-delete time from config
            delete_time = self.config.get('auto_delete_time', 30)
            info_msg = await update.message.reply_text(
                f"⚠️ These files will be automatically deleted after {delete_time} minute{'s' if delete_time != 1 else ''}!\n"
                f"🔄 Forward this File to save the files.\n\n"
                f"⚠️ এই ফাইলগুলি {delete_time} মিনিট পর স্বয়ংক্রিয়ভাবে মুছে ফেলা হবে!\n"
                f"🔄 ফাইলগুলি সংরক্ষণ করতে ফাইলগুলি ফরওয়ার্ড করুন।"
            )
            sent_messages.append(info_msg)
            
            for file_info in batch_doc['files']:
                try:
                    file_type = file_info.get('file_type', 'document')
                    caption = file_info.get('caption', '')
                    prefix_name = self.config.get('prefix_name', '@CinemazBD')
                    
                    # Remove configured names from caption before sending
                    if caption:
                        remove_names = self.config.get('remove_names', [])
                        caption_lower = caption.lower()
                        for name in remove_names:
                            if name.lower() in caption_lower:
                                caption = caption.replace(name, '').replace('  ', ' ').strip()
                                caption_lower = caption.lower()
                    
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