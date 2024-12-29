from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
import json
import os
import asyncio

class BotSettings:
    def __init__(self, config):
        self.config = config
        self.waiting_for_input = {}  # Track users waiting for input
    
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bset command"""
        if not await self._is_admin(update.effective_user.id):
            await update.message.reply_text("You don't have permission to use this command!")
            return
        
        # Show settings menu
        await self._show_settings_menu(update)
    
    async def _show_settings_menu(self, update: Update):
        """Show settings menu with buttons"""
        current_settings = {
            'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
            'Prefix': self.config.get('prefix_name') or 'Not set',
            'Sudo Users': len(self.config.get('sudo_users', [])),
            'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled'
        }
        
        text = "🛠 <b>Bot Settings</b>\n\n"
        for key, value in current_settings.items():
            text += f"• <b>{key}:</b> {value}\n"
        
        keyboard = [
            [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
            [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
            [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
            [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
            [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
            [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from settings buttons"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "setting_close":
            await query.message.delete()
            return
        
        if query.data == "setting_view_all":
            settings = {
                "Auto Delete Time": f"{self.config.get('auto_delete_time')} minutes",
                "Prefix Name": self.config.get('prefix_name') or 'Not set',
                "Sudo Users": self.config.get('sudo_users', []),
                "Shortener": {
                    "Status": "Enabled" if self.config.get('shortener', {}).get('enabled') else "Disabled",
                    "API URL": self.config.get('shortener', {}).get('api_url', '')
                }
            }
            text = "📊 <b>Current Settings</b>\n\n"
            text += json.dumps(settings, indent=2)
            keyboard = [
                [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
        
        if query.data == "setting_menu":
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled'
            }
            
            text = "🛠 <b>Bot Settings</b>\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            except BadRequest as e:
                if str(e) != "Message is not modified":
                    raise e
            return
        
        # Handle reset button clicks
        if query.data.startswith('reset_'):
            setting_type = query.data.split('_')[1]
            await self.handle_reset(query, setting_type)
            return
        
        # Handle settings editors
        if query.data.startswith('setting_'):
            setting_type = query.data.replace('setting_', '')
            await self._show_setting_editor(query.message, setting_type, update.effective_user.id)
            return
    
    async def _show_setting_editor(self, message, setting_type, user_id):
        """Show editor for specific setting"""
        try:
            print(f"Showing editor for setting type: {setting_type}")  # Debug print
            
            keyboard = [
                [InlineKeyboardButton("🔄 Reset to Default", callback_data=f"reset_{setting_type}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="setting_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = ""
            
            if setting_type == "auto_delete":
                current = self.config.get('auto_delete_time')
                text = (
                    f"⏱ <b>Auto Delete Settings</b>\n\n"
                    f"Current time: <b>{current} minutes</b>\n\n"
                    f"Send a new value in minutes (1-1440).\n"
                    f"Example: <code>30</code> for 30 minutes"
                )
                
            elif setting_type == "prefix":
                current = self.config.get('prefix_name')
                text = (
                    f"📝 <b>Prefix Settings</b>\n\n"
                    f"Current prefix: <b>{current or 'Not set'}</b>\n\n"
                    f"Send a new prefix.\n"
                    f"Example: <code>@YourChannel</code>"
                )
                
            elif setting_type == "sudo":
                current = self.config.get('sudo_users', [])
                text = (
                    f"👥 <b>Sudo Users Settings</b>\n\n"
                    f"Current users: <b>{current}</b>\n\n"
                    f"Send user IDs separated by commas.\n"
                    f"Example: <code>123456789,987654321</code>"
                )
                
            elif setting_type == "shortener":
                current = self.config.get('shortener', {})
                text = (
                    f"🔗 <b>Shortener Settings</b>\n\n"
                    f"Status: <b>{'Enabled' if current.get('enabled') else 'Disabled'}</b>\n"
                    f"API Key: <code>{current.get('api_key', '')}</code>\n"
                    f"API URL: <code>{current.get('api_url', '')}</code>\n\n"
                    f"Send new settings in format:\n"
                    f"<code>enabled/disabled,api_key,api_url</code>\n\n"
                    f"Example:\n<code>enabled,your_api_key,https://example.com/api</code>"
                )
            
            if not text:
                raise ValueError(f"Invalid setting type: {setting_type}")
            
            await message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
            # Set waiting for input with message
            self.waiting_for_input[user_id] = {
                'type': setting_type,
                'message': message,
                'expires': asyncio.create_task(self._expire_input(user_id, message))
            }
            
        except Exception as e:
            print(f"Error in _show_setting_editor: {str(e)}")  # Debug print
            print(f"Setting type: {setting_type}")  # Debug print
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="setting_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.edit_text(
                f"❌ Error showing settings editor: {str(e)}\nPlease try again.",
                reply_markup=reply_markup
            )
    
    async def _expire_input(self, user_id, message):
        """Expire input after 60 seconds"""
        await asyncio.sleep(60)
        if user_id in self.waiting_for_input:
            del self.waiting_for_input[user_id]
            keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="setting_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.edit_text("Setting update timeout. Please try again.", reply_markup=reply_markup)
    
    async def handle_setting_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle setting update messages"""
        user_id = update.effective_user.id
        if user_id not in self.waiting_for_input:
            return
            
        setting_info = self.waiting_for_input[user_id]
        setting_type = setting_info['type']
        value = update.message.text.strip()
        message = setting_info['message']
        
        # Delete user's input message
        try:
            await update.message.delete()
        except:
            pass
        
        # Cancel expiry task
        setting_info['expires'].cancel()
        
        try:
            if setting_type == "auto_delete":
                minutes = int(value)
                if minutes < 1:
                    raise ValueError("Minutes must be positive")
                self.config.set('auto_delete_time', minutes)
                success = f"✅ Auto delete time set to {minutes} minutes"
                
            elif setting_type == "prefix":
                self.config.set('prefix_name', value)
                success = f"✅ Prefix name set to: {value}"
                
            elif setting_type == "sudo":
                user_ids = [int(id.strip()) for id in value.split(',') if id.strip()]
                self.config.set('sudo_users', user_ids)
                success = f"✅ Added {len(user_ids)} sudo users"
                
            elif setting_type == "shortener":
                enabled, api_key, api_url = value.split(',')
                self.config.set('shortener', {
                    'enabled': enabled.lower() == 'enabled',
                    'api_key': api_key.strip(),
                    'api_url': api_url.strip()
                })
                success = "✅ Shortener settings updated successfully"
            
            # Show updated settings menu
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled'
            }
            
            text = f"🛠 <b>Bot Settings</b>\n\n{success}\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
        except Exception as e:
            text = f"❌ Error: {str(e)}\n\nPlease try again"
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"setting_{setting_type}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="setting_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        del self.waiting_for_input[user_id]
    
    async def handle_reset(self, query, setting_type):
        """Handle reset button clicks"""
        try:
            if setting_type == "shortener":
                self.config.set('shortener', {
                    'enabled': False,
                    'api_key': '',
                    'api_url': 'https://example.com/api'
                })
                success = "✅ Shortener settings reset to default!"
            elif setting_type == "auto_delete":
                self.config.set('auto_delete_time', 30)
                success = "✅ Auto delete time reset to default (30 minutes)!"
            elif setting_type == "prefix":
                self.config.set('prefix_name', '')
                success = "✅ Prefix name reset to default (empty)!"
            elif setting_type == "sudo":
                self.config.set('sudo_users', [])
                success = "✅ Sudo users list cleared!"
            
            # Show updated settings menu with success message
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled'
            }
            
            text = f"🛠 <b>Bot Settings</b>\n\n{success}\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            print(f"Error in handle_reset: {str(e)}")
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="setting_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"❌ Error resetting settings: {str(e)}\nPlease try again.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        admin_id = int(os.getenv('ADMIN_ID', '0'))
        sudo_users = self.config.get('sudo_users', [])
        return user_id == admin_id or user_id in sudo_users 

    def _load_config(self):
        """Load config from database or create default"""
        config = self.config_collection.find_one({'_id': 'bot_config'})
        if not config:
            default_config = {
                '_id': 'bot_config',
                'auto_delete_time': int(os.getenv('AUTO_DELETE_TIME', '30')),
                'prefix_name': os.getenv('PREFIX_NAME', ''),
                'sudo_users': [],
                'shortener': {
                    'enabled': False,
                    'api_key': '',
                    'api_url': 'https://example.com/api'  # Changed default URL
                }
            }
            self.config_collection.insert_one(default_config)
            self.config = default_config
        else:
            self.config = config 