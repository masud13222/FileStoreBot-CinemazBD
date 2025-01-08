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
            'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled',
            'Remove Names': len(self.config.get('remove_names', [])),
            'Link Saving': 'ON' if self.config.get('link_enabled', True) else 'OFF'
        }
        
        text = "🛠 <b>Bot Settings</b>\n\n"
        for key, value in current_settings.items():
            text += f"• <b>{key}:</b> {value}\n"
        
        keyboard = [
            [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
            [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
            [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
            [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
            [InlineKeyboardButton("🗑 Remove Names", callback_data="setting_remname")],
            [InlineKeyboardButton("🔗 Link Saving", callback_data="toggle_link_saving")],
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
            
        if query.data == "toggle_link_saving":
            current_state = self.config.get('link_enabled', True)
            new_state = not current_state
            self.config.set('link_enabled', new_state)
            # Update settings menu
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled',
                'Remove Names': len(self.config.get('remove_names', [])),
                'Link Saving': 'ON' if new_state else 'OFF'
            }
            
            text = "🛠 <b>Bot Settings</b>\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("🗑 Remove Names", callback_data="setting_remname")],
                [InlineKeyboardButton("🔗 Link Saving", callback_data="toggle_link_saving")],
                [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
            
        if query.data == "setting_menu":
            # Update settings menu
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled',
                'Remove Names': len(self.config.get('remove_names', [])),
                'Link Saving': 'ON' if self.config.get('link_enabled', True) else 'OFF'
            }
            
            text = "🛠 <b>Bot Settings</b>\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("🗑 Remove Names", callback_data="setting_remname")],
                [InlineKeyboardButton("🔗 Link Saving", callback_data="toggle_link_saving")],
                [InlineKeyboardButton("📊 View All Settings", callback_data="setting_view_all")],
                [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
            
        if query.data == "setting_view_all":
            settings = {
                "Auto Delete Time": f"{self.config.get('auto_delete_time')} minutes",
                "Prefix Name": self.config.get('prefix_name') or 'Not set',
                "Sudo Users": self.config.get('sudo_users', []),
                "Shortener": {
                    "Status": "Enabled" if self.config.get('shortener', {}).get('enabled') else "Disabled",
                    "API URL": self.config.get('shortener', {}).get('api_url', '')
                },
                "Remove Names": self.config.get('remove_names', []),
                "Link Saving": "ON" if self.config.get('link_enabled', True) else "OFF"
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
            text = ""
            keyboard = []
            
            if setting_type == "shortener":
                shortener = self.config.get('shortener', {})
                enabled = shortener.get('enabled', False)
                api_key = shortener.get('api_key', '')
                api_url = shortener.get('api_url', '')
                
                text = (
                    f"🔗 <b>URL Shortener Settings</b>\n\n"
                    f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
                    f"API Key: <code>{api_key or 'Not set'}</code>\n"
                    f"API URL: <code>{api_url or 'Not set'}</code>\n\n"
                    "Send settings in this format:\n"
                    "<code>enable/disable</code> - To toggle shortener\n"
                    "<code>key YOUR_API_KEY</code> - To set API key\n"
                    "<code>url API_URL</code> - To set API URL\n\n"
                    "Example:\n"
                    "<code>enable</code>\n"
                    "<code>key abc123</code>\n"
                    "<code>url https://example.com/api</code>"
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_shortener")],
                    [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]
                ]
                
            elif setting_type == "auto_delete":
                current_time = self.config.get('auto_delete_time')
                text = (
                    f"⏱ <b>Auto Delete Time Settings</b>\n\n"
                    f"Current time: {current_time} minutes\n\n"
                    "Send a number between 1-10000 to set auto delete time in minutes.\n"
                    "Send 0 to disable auto delete."
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_auto_delete")],
                    [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]
                ]
                
            elif setting_type == "prefix":
                current_prefix = self.config.get('prefix_name') or 'Not set'
                text = (
                    f"📝 <b>Prefix Name Settings</b>\n\n"
                    f"Current prefix: {current_prefix}\n\n"
                    "Send new prefix name or 'clear' to remove prefix."
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_prefix")],
                    [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]
                ]
                
            elif setting_type == "sudo":
                current_users = self.config.get('sudo_users', [])
                text = (
                    f"👥 <b>Sudo Users Settings</b>\n\n"
                    f"Current sudo users:\n"
                )
                if current_users:
                    for i, user_id in enumerate(current_users, 1):
                        text += f"{i}. <code>{user_id}</code>\n"
                else:
                    text += "No sudo users configured\n"
                
                text += "\nSend user IDs separated by commas to add/remove.\n"
                text += "Example: <code>123456789,987654321</code>"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_sudo")],
                    [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]
                ]
                
            elif setting_type == "remname":
                current_names = self.config.get('remove_names', [])
                text = (
                    f"🗑 <b>Remove Names Settings</b>\n\n"
                    f"Current names to remove:\n"
                )
                if current_names:
                    for i, name in enumerate(current_names, 1):
                        text += f"{i}. <code>{name}</code>\n"
                else:
                    text += "No names configured yet\n"
                
                text += "\nSend names to add/remove separated by commas.\n"
                text += "Example: <code>mkvcinemas,telly</code>\n"
                text += "\nTo clear all names, send: <code>clear</code>"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_remname")],
                    [InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]
                ]
            
            if not text:
                raise ValueError(f"Invalid setting type: {setting_type}")
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
            # Set waiting for input
            self.waiting_for_input[user_id] = {
                'type': setting_type,
                'message': message,
                'expires': asyncio.create_task(self._expire_input(user_id, message))
            }
            
        except Exception as e:
            print(f"Error in _show_setting_editor: {str(e)}")
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="setting_menu")]]
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
        """Handle settings update from user input"""
        try:
            user_id = update.effective_user.id
            if user_id not in self.waiting_for_input:
                return
                
            setting_info = self.waiting_for_input[user_id]
            setting_type = setting_info['type']
            message = setting_info['message']
            success = None
            
            if setting_type == "shortener":
                text = update.message.text.lower().strip()
                shortener = self.config.get('shortener', {})
                
                if text == 'enable':
                    shortener['enabled'] = True
                    success = "✅ Shortener enabled!"
                elif text == 'disable':
                    shortener['enabled'] = False
                    success = "✅ Shortener disabled!"
                elif text.startswith('key '):
                    api_key = text[4:].strip()
                    shortener['api_key'] = api_key
                    success = "✅ API key updated!"
                elif text.startswith('url '):
                    api_url = text[4:].strip()
                    shortener['api_url'] = api_url
                    success = "✅ API URL updated!"
                else:
                    await update.message.reply_text(
                        "❌ Invalid format! Please use:\n"
                        "<code>enable</code> or <code>disable</code> - To toggle shortener\n"
                        "<code>key YOUR_API_KEY</code> - To set API key\n"
                        "<code>url API_URL</code> - To set API URL",
                        parse_mode='HTML'
                    )
                    return
                    
                self.config.set('shortener', shortener)
                
            elif setting_type == "auto_delete":
                try:
                    minutes = int(update.message.text)
                    if minutes < 0 or minutes > 10000:
                        raise ValueError("Time must be between 0-10000 minutes")
                    self.config.set('auto_delete_time', minutes)
                    success = f"✅ Auto delete time set to {minutes} minutes!"
                except ValueError as e:
                    await update.message.reply_text(f"❌ Invalid time: {str(e)}")
                    return
                    
            elif setting_type == "prefix":
                self.config.set('prefix_name', update.message.text.strip())
                success = f"✅ Prefix name set to: {update.message.text.strip()}"
                
            elif setting_type == "sudo":
                user_ids = [int(id.strip()) for id in update.message.text.split(',') if id.strip()]
                self.config.set('sudo_users', user_ids)
                success = f"✅ Added {len(user_ids)} sudo users"
                
            elif setting_type == "remname":
                if update.message.text.lower() == 'clear':
                    self.config.set('remove_names', [])
                    success = "✅ Cleared all remove names"
                else:
                    names = [n.strip() for n in update.message.text.split(',') if n.strip()]
                    current_names = self.config.get('remove_names', [])
                    
                    # Add new names and remove duplicates
                    current_names.extend(names)
                    current_names = list(set(current_names))
                    
                    self.config.set('remove_names', current_names)
                    success = f"✅ Updated remove names list. Total names: {len(current_names)}"
            
            # Show updated settings menu
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled',
                'Remove Names': len(self.config.get('remove_names', [])),
                'Link Saving': 'ON' if self.config.get('link_enabled', True) else 'OFF'
            }
            
            text = f"🛠 <b>Bot Settings</b>\n\n{success}\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("🗑 Remove Names", callback_data="setting_remname")],
                [InlineKeyboardButton("🔗 Link Saving", callback_data="toggle_link_saving")],
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
            elif setting_type == "remname":
                self.config.set('remove_names', [])
                success = "✅ Remove names list cleared!"
            
            # Show updated settings menu with success message
            current_settings = {
                'Auto Delete': f"{self.config.get('auto_delete_time')} minutes",
                'Prefix': self.config.get('prefix_name') or 'Not set',
                'Sudo Users': len(self.config.get('sudo_users', [])),
                'Shortener': 'Enabled' if self.config.get('shortener', {}).get('enabled') else 'Disabled',
                'Remove Names': len(self.config.get('remove_names', [])),
                'Link Saving': 'ON' if self.config.get('link_enabled', True) else 'OFF'
            }
            
            text = f"🛠 <b>Bot Settings</b>\n\n{success}\n\n"
            for key, value in current_settings.items():
                text += f"• <b>{key}:</b> {value}\n"
            
            keyboard = [
                [InlineKeyboardButton("⏱ Auto Delete Time", callback_data="setting_auto_delete")],
                [InlineKeyboardButton("📝 Prefix Name", callback_data="setting_prefix")],
                [InlineKeyboardButton("👥 Sudo Users", callback_data="setting_sudo")],
                [InlineKeyboardButton("🔗 Shortener Settings", callback_data="setting_shortener")],
                [InlineKeyboardButton("🗑 Remove Names", callback_data="setting_remname")],
                [InlineKeyboardButton("🔗 Link Saving", callback_data="toggle_link_saving")],
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