from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config.database import connect_db
import os
from dotenv import load_dotenv
from helpers.batch_handler import BatchHandler
import asyncio
from helpers.user_handler import UserHandler
from helpers.broadcast_handler import BroadcastHandler
from helpers.auto_delete_handler import AutoDeleteHandler
from config.config import Config
from helpers.bot_settings import BotSettings
from helpers.shortener import Shortener
from helpers.delete_handler import DeleteHandler
from helpers.direct_link_handler import DirectLinkHandler
from aiohttp import web
import subprocess
import sys
from restart import restart
from helpers.caption_handler import CaptionHandler

# Load environment variables
load_dotenv()

# Connect to MongoDB
db = connect_db()
files_collection = db['files']

# Initialize config first
config = Config(db)

# Initialize all handlers
batch_handler = BatchHandler(db, config)
user_handler = UserHandler(db)
broadcast_handler = BroadcastHandler(db)
auto_delete_handler = AutoDeleteHandler(db)
bot_settings = BotSettings(config)
shortener = Shortener(config)
delete_handler = DeleteHandler(db, config)
direct_link_handler = DirectLinkHandler(config)
caption_handler = CaptionHandler(config)

def is_authorized(user_id: int) -> bool:
    """Check if user is admin or sudo user"""
    admin_id = int(os.getenv('ADMIN_ID', '0'))
    sudo_users = config.get('sudo_users', [])
    return user_id == admin_id or user_id in sudo_users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    # Add user to database
    await user_handler.handle_new_user(
        update.effective_user.id,
        update.effective_user.username
    )
    
    if len(context.args) > 0:
        arg = context.args[0]
        
        # Check if it's a batch link
        if arg.startswith('batch_'):
            batch_code = arg[6:]  # Remove 'batch_' prefix
            batch_doc = db['batches'].find_one({"batch_code": batch_code})
            
            if batch_doc:
                await batch_handler.handle_batch_start(update, context, batch_doc)
            else:
                await update.message.reply_text("Batch not found!")
            return
                
        # Regular single file handling continues here...
        file_doc = files_collection.find_one({"file_code": arg})
        
        if file_doc:
            try:
                sent_messages = []
                
                # Fetch auto-delete time from config
                delete_time = config.get('auto_delete_time', 30)
                info_msg = await update.message.reply_text(
                    f"⚠️ This file will be automatically deleted after {delete_time} minute{'s' if delete_time != 1 else ''}!\n"
                    f"🔄 Forward this File to save the file.\n\n"
                    f"⚠️ এই ফাইলটি {delete_time} মিনিট পর স্বয়ংক্রিয়ভাবে মুছে ফেলা হবে!\n"
                    f"🔄 ফাইলটি সংরক্ষণ করতে ফাইলগুলি ফরওয়ার্ড করুন।"
                )
                sent_messages.append(info_msg)
                
                # Get file info
                file_type = file_doc.get('file_type', 'document')
                caption = file_doc.get('caption', '')
                prefix_name = config.get('prefix_name', '@CinemazBD')
                
                # Remove configured names from caption before sending
                if caption:
                    remove_names = config.get('remove_names', [])
                    caption_lower = caption.lower()
                    for name in remove_names:
                        if name.lower() in caption_lower:
                            caption = caption.replace(name, '').replace('  ', ' ').strip()
                            caption_lower = caption.lower()
                
                # Format caption
                if caption:
                    caption = f"{prefix_name} - {caption}"  # Add prefix with hyphen
                else:
                    caption = f"{prefix_name}\n<b>Here's your file!</b>"
                
                # Make the whole caption bold
                caption = f"<b>{caption}</b>"
                
                if file_type == 'photo':
                    sent_msg = await update.message.reply_photo(
                        photo=file_doc['file_id'],
                        caption=caption,
                        parse_mode='HTML'
                    )
                elif file_type == 'video':
                    sent_msg = await update.message.reply_video(
                        video=file_doc['file_id'],
                        caption=caption,
                        parse_mode='HTML'
                    )
                elif file_type == 'audio':
                    sent_msg = await update.message.reply_audio(
                        audio=file_doc['file_id'],
                        caption=caption,
                        parse_mode='HTML'
                    )
                else:
                    sent_msg = await update.message.reply_document(
                        document=file_doc['file_id'],
                        caption=caption,
                        parse_mode='HTML'
                    )
                    
                # Add sent file message to list
                sent_messages.append(sent_msg)
                
                # Schedule messages for auto-deletion
                await auto_delete_handler.handle_shared_files(sent_messages)
                
            except Exception as e:
                print(f"Error sending file: {str(e)}")
                await update.message.reply_text("Sorry, couldn't send the file!")
        else:
            await update.message.reply_text("File not found!")
    else:
        await update.message.reply_text(
            "👋 Welcome to the CinemazBD Bot!\n\n"
            "📤 Send me any file and I'll provide you with a shareable link.\n\n"
            "🌐 আপনাকে স্বাগতম! আমাকে যেকোনো ফাইল পাঠান এবং আমি আপনাকে একটি শেয়ারযোগ্য লিঙ্ক দেব।\n\n"
            "🔗 Enjoy sharing your files easily! @CinemazBD"
        )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files sent to the bot."""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("You don't have permission to use this feature!")
        return

    message = update.message
    file = None
    file_type = None

    # Check for different types of files
    if message.document:
        file = message.document
        file_type = "document"
    elif message.video:
        file = message.video
        file_type = "video"
    elif message.audio:
        file = message.audio
        file_type = "audio"
    elif message.photo:
        file = message.photo[-1]
        file_type = "photo"
    elif message.voice:
        file = message.voice
        file_type = "voice"
    elif message.video_note:
        file = message.video_note
        file_type = "video_note"

    if file:
        try:
            file_code = str(abs(hash(file.file_id)))[:8]
            
            # Process caption to remove configured names
            caption = message.caption
            if caption:
                remove_names = config.get('remove_names', [])
                caption_lower = caption.lower()
                for name in remove_names:
                    if name.lower() in caption_lower:
                        caption = caption.replace(name, '').replace('  ', ' ').strip()
                        caption_lower = caption.lower()
            
            # Save to database
            files_collection.insert_one({
                "file_id": file.file_id,
                "file_code": file_code,
                "file_type": file_type,
                "file_name": getattr(file, 'file_name', None),
                "mime_type": getattr(file, 'mime_type', None),
                "caption": caption,
                "user_id": update.message.from_user.id
            })
            
            # Generate permanent link using worker URL
            worker_url = os.getenv('WORKER_URL', '').rstrip('/')
            share_link = f"{worker_url}/{file_code}"
            
            # Shorten the link if enabled
            shortened_link = await shortener.shorten_url(share_link)
            
            # Prepare file name or caption
            file_name_or_caption = caption or getattr(file, 'file_name', 'No Name')
            
            await update.message.reply_text(
                f"Here's your permanent shareable link:\n{shortened_link}\n\nFile: {file_name_or_caption}"
            )
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await update.message.reply_text(
                "Sorry, there was an error processing your file."
            )

# Add error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    print(f"Update {update} caused error {context.error}")

async def authorized_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command_func):
    """Wrapper to check if user is authorized before executing command."""
    if is_authorized(update.effective_user.id):
        await command_func(update, context)
    else:
        await update.message.reply_text("You don't have permission to use this command!")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot if the user is authorized."""
    if is_authorized(update.effective_user.id):
        await update.message.reply_text("Restarting the bot...")
        restart()
    else:
        await update.message.reply_text("You don't have permission to restart the bot!")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("batch", lambda u, c: authorized_command(u, c, batch_handler.handle_batch_command)))
    application.add_handler(CommandHandler("setcaption", lambda u, c: authorized_command(u, c, caption_handler.handle_setcaption_command)))
    
    # Update file handler
    async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # First check if this is for caption change
        if await caption_handler.handle_file_for_caption(update, context):
            return
            
        # Then try batch handler
        is_batch = await batch_handler.handle_batch_file(update, context)
        if not is_batch:
            # If not part of batch, handle as single file
            await handle_file(update, context)
    
    application.add_handler(MessageHandler(
        (filters.AUDIO | 
         filters.Document.ALL | 
         filters.PHOTO | 
         filters.VIDEO | 
         filters.VOICE | 
         filters.VIDEO_NOTE),
        file_handler
    ))

    # Add new handlers
    application.add_handler(CommandHandler("users", lambda u, c: authorized_command(u, c, user_handler.get_users_count)))
    application.add_handler(CommandHandler("broadcast", lambda u, c: authorized_command(u, c, broadcast_handler.broadcast_message)))

    # Add settings handler
    application.add_handler(CommandHandler("bset", lambda u, c: authorized_command(u, c, bot_settings.handle_settings)))
    application.add_handler(CallbackQueryHandler(bot_settings.handle_callback))

    # Add message handler for settings update
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda u, c: caption_handler.handle_caption_update(u, c) if u.effective_user.id in caption_handler.waiting_for_caption else bot_settings.handle_setting_update(u, c)
    ))

    # Add error handler
    application.add_error_handler(error_handler)

    # Add delete handler
    application.add_handler(CommandHandler("del", lambda u, c: authorized_command(u, c, delete_handler.handle_delete)))

    # Add direct link handler
    application.add_handler(CommandHandler("gdirect", lambda u, c: authorized_command(u, c, direct_link_handler.handle_direct_link_command)))

    # Add restart handler
    application.add_handler(CommandHandler("restart", restart_command))

    # Start the Bot
    print("Bot is running...")
    application.run_polling()

# Define a simple health check endpoint
async def health_check(request):
    return web.Response(text="OK")

# Create an aiohttp web application
app = web.Application()
app.router.add_get('/health', health_check)

# Function to run the web server
def run_web_server():
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    loop.run_until_complete(site.start())
    print("Health check server running on port 8080")

# Call the function to run the web server
run_web_server()

if __name__ == '__main__':
    main() 