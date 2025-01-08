from telegram import Update
from telegram.ext import ContextTypes
import os

class CaptionHandler:
    def __init__(self, config):
        self.config = config
        self.waiting_for_file = set()  # Users waiting to send file
        self.waiting_for_caption = {}  # Users waiting to send caption with file info

    async def handle_setcaption_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setcaption command"""
        user_id = update.effective_user.id
        
        # Check if admin
        if not await self._is_admin(user_id):
            await update.message.reply_text("You don't have permission to use this command!")
            return
        
        # Add user to waiting list
        self.waiting_for_file.add(user_id)
        
        await update.message.reply_text(
            "📤 Send me the file you want to change the caption of.\n\n"
            "📤 যে ফাইলের ক্যাপশন পরিবর্তন করতে চান সেই ফাইলটি পাঠান।"
        )
    
    async def handle_file_for_caption(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file received for caption change"""
        user_id = update.effective_user.id
        
        if user_id not in self.waiting_for_file:
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
            
            await update.message.reply_text(
                "✏️ Now send me the new caption for this file.\n\n"
                "✏️ এখন এই ফাইলের জন্য নতুন ক্যাপশন পাঠান।"
            )
            return True
            
        return False
    
    async def handle_caption_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new caption for file"""
        user_id = update.effective_user.id
        
        if user_id not in self.waiting_for_caption:
            return False
            
        file_info = self.waiting_for_caption[user_id]
        new_caption = update.message.text
        
        try:
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
            
            # Remove user from waiting list
            del self.waiting_for_caption[user_id]
            
            await update.message.reply_text(
                "✅ Caption updated successfully!\n\n"
                "✅ ক্যাপশন সফলভাবে আপডেট করা হয়েছে!"
            )
            
        except Exception as e:
            print(f"Error sending file: {str(e)}")
            await update.message.reply_text(
                "❌ Failed to send file with new caption.\n\n"
                "❌ নতুন ক্যাপশন সহ ফাইল পাঠানো যায়নি।"
            )
            del self.waiting_for_caption[user_id]
        
        return True
    
    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        sudo_users = self.config.get('sudo_users', [])
        return user_id == admin_id or user_id in sudo_users 