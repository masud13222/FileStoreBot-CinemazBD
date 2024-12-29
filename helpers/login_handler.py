from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import Update
from telegram.ext import ContextTypes
import os

class LoginHandler:
    def __init__(self, db):
        self.client = TelegramClient('session_name', os.getenv('API_ID'), os.getenv('API_HASH'))
        self.is_logged_in = False
        self.db = db

    async def handle_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle login process"""
        await update.message.reply_text("Please enter your phone number:")
        context.user_data['awaiting_phone'] = True

    async def check_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check the entered phone number and send code"""
        if context.user_data.get('awaiting_phone'):
            phone = update.message.text
            try:
                await self.client.start(phone)
                await update.message.reply_text("A code has been sent to your phone. Please enter the code:")
                context.user_data['awaiting_phone'] = False
                context.user_data['awaiting_code'] = True
            except Exception as e:
                await update.message.reply_text(f"Failed to send code: {str(e)}")

    async def check_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check the entered code"""
        if context.user_data.get('awaiting_code'):
            code = update.message.text
            try:
                await self.client.sign_in(code=code)
                self.is_logged_in = True
                await update.message.reply_text("Login successful! ✅")
                self.save_login_info(update.effective_user.id)
            except SessionPasswordNeededError:
                await update.message.reply_text("Two-step verification is enabled. Please enter your password:")
                context.user_data['awaiting_password'] = True
            except Exception as e:
                await update.message.reply_text(f"Login failed: {str(e)}")
            context.user_data['awaiting_code'] = False

    async def check_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check the entered password for two-step verification"""
        if context.user_data.get('awaiting_password'):
            password = update.message.text
            try:
                await self.client.sign_in(password=password)
                self.is_logged_in = True
                await update.message.reply_text("Login successful! ✅")
                self.save_login_info(update.effective_user.id)
            except Exception as e:
                await update.message.reply_text(f"Login failed: {str(e)}")
            context.user_data['awaiting_password'] = False

    def save_login_info(self, user_id):
        """Save login information to the database"""
        self.db['logins'].insert_one({'user_id': user_id, 'is_logged_in': True})
