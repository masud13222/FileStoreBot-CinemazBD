from telegram import Update
from telegram.ext import ContextTypes
import os
import time
import asyncio

class CaptionHandler:
    def __init__(self, config):
        self.config = config
        self.waiting_for_file = set()  # Users waiting to send file
        self.waiting_for_caption = {}  # Users waiting to send caption with file info
        self.start_times = {}  # Store start times for timeout
        self.status_messages = {}  # Store status messages for updates

    async def handle_setcaption_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setcaption command"""
        user_id = update.effective_user.id
        
        # Check if admin
        if not await self._is_admin(user_id):
            await update.message.reply_text("You don't have permission to use this command!")
            return

        # Add user to waiting list
        self.waiting_for_file.add(user_id)
        self.start_times[user_id] = time.time()
        
        # Send initial message and store it
        status_msg = await update.message.reply_text(
            "📤 Send me the file you want to change the caption of.\n"
            "⏳ Time remaining: 60 seconds"
        )
        self.status_messages[user_id] = status_msg
        
        # Start timeout checker
        asyncio.create_task(self._check_timeout(user_id))

    async def _check_timeout(self, user_id: int):
        """Check for timeout and update message"""
        last_remaining = None
        
        while user_id in self.waiting_for_file or user_id in self.waiting_for_caption:
            elapsed = time.time() - self.start_times[user_id]
            if elapsed >= 60:
                # Handle timeout
                if user_id in self.status_messages:
                    try:
                        await self.status_messages[user_id].edit_text(
                            "❌ Time's up! Please use /setcaption command again."
                        )
                    except Exception:
                        pass  # Ignore edit message errors
                    del self.status_messages[user_id]
                
                # Clean up
                if user_id in self.waiting_for_file:
                    self.waiting_for_file.remove(user_id)
                if user_id in self.waiting_for_caption:
                    del self.waiting_for_caption[user_id]
                if user_id in self.start_times:
                    del self.start_times[user_id]
                break
            
            # Update remaining time every 5 seconds
            if user_id in self.status_messages:
                remaining = 60 - int(elapsed)
                # Only update if remaining time has changed
                if remaining != last_remaining:
                    msg = self.status_messages[user_id]
                    try:
                        if user_id in self.waiting_for_file:
                            await msg.edit_text(
                                "📤 Send me the file you want to change the caption of.\n"
                                f"⏳ Time remaining: {remaining} seconds"
                            )
                        elif user_id in self.waiting_for_caption:
                            await msg.edit_text(
                                "✏️ Now send me the new caption for this file.\n"
                                f"⏳ Time remaining: {remaining} seconds"
                            )
                        last_remaining = remaining
                    except Exception:
                        pass  # Ignore edit message errors
            await asyncio.sleep(5)

    async def handle_file_for_caption(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file received for caption change"""
        user_id = update.effective_user.id
        
        if user_id not in self.waiting_for_file:
            return False
            
        # Check for timeout
        if time.time() - self.start_times[user_id] >= 60:
            return False
            
        message = update.message
        file_info = None
        
        # Get file info based on type
        if message.document:
            file_info = {'file': message.document, 'type': 'document'}
        elif message.video:
            file_info = {'file': message.video, 'type': 'video'}
        elif message.audio:
            file_info = {'file': message.audio, 'type': 'audio'}
        elif message.photo:
            file_info = {'file': message.photo[-1], 'type': 'photo'}
        elif message.voice:
            file_info = {'file': message.voice, 'type': 'voice'}
        elif message.video_note:
            file_info = {'file': message.video_note, 'type': 'video_note'}
            
        if file_info:
            # Remove from waiting for file list
            self.waiting_for_file.remove(user_id)
            
            # Add to waiting for caption list with file info
            self.waiting_for_caption[user_id] = file_info
            
            # Reset timer for caption input
            self.start_times[user_id] = time.time()
            
            # Delete old message and send new one
            if user_id in self.status_messages:
                await self.status_messages[user_id].delete()
            
            new_msg = await message.reply_text(
                "✏️ Now send me the new caption for this file.\n"
                "⏳ Time remaining: 60 seconds"
            )
            self.status_messages[user_id] = new_msg
            return True
            
        return False

    async def handle_caption_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new caption for file"""
        user_id = update.effective_user.id
        
        if user_id not in self.waiting_for_caption:
            return False
            
        # Check for timeout
        if time.time() - self.start_times[user_id] >= 60:
            return False
            
        file_info = self.waiting_for_caption[user_id]
        new_caption = update.message.text
        
        try:
            # Delete the status message
            if user_id in self.status_messages:
                await self.status_messages[user_id].delete()
            
            # Make caption bold without prefix
            caption = f"<b>{new_caption}</b>"
            
            # Send file with new caption
            if file_info['type'] == 'photo':
                await update.message.reply_photo(
                    photo=file_info['file'].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif file_info['type'] == 'video':
                await update.message.reply_video(
                    video=file_info['file'].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif file_info['type'] == 'audio':
                await update.message.reply_audio(
                    audio=file_info['file'].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif file_info['type'] == 'voice':
                await update.message.reply_voice(
                    voice=file_info['file'].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif file_info['type'] == 'video_note':
                await update.message.reply_video_note(
                    video_note=file_info['file'].file_id
                )
            else:
                await update.message.reply_document(
                    document=file_info['file'].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            
            # Send success message
            success_msg = await update.message.reply_text(
                "✅ Caption updated successfully!"
            )
            
            # Clean up
            del self.waiting_for_caption[user_id]
            if user_id in self.start_times:
                del self.start_times[user_id]
            
        except Exception as e:
            print(f"Error sending file: {str(e)}")
            error_msg = await update.message.reply_text(
                "❌ Failed to send file with new caption."
            )
            # Clean up on error
            if user_id in self.waiting_for_caption:
                del self.waiting_for_caption[user_id]
            if user_id in self.start_times:
                del self.start_times[user_id]
            
        return True

    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        sudo_users = self.config.get('sudo_users', [])
        return user_id == admin_id or user_id in sudo_users 