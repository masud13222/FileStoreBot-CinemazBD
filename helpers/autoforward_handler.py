from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from helpers.login_handler import LoginHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoForwardHandler:
    def __init__(self, config, db):
        self.config = config
        self.target_channel = None
        self.source_channels = []
        self.login_handler = LoginHandler(db)

    async def handle_autoforward_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autoforward command"""
        keyboard = [
            [InlineKeyboardButton("🔑 Login", callback_data='login')],
            [InlineKeyboardButton("🎯 Set Target", callback_data='set_target')],
            [InlineKeyboardButton("📥 Set Source", callback_data='set_source')],
            [InlineKeyboardButton("▶️ Run", callback_data='run')],
            [InlineKeyboardButton("❌ Close", callback_data='close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Choose an option:', reply_markup=reply_markup)

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        logger.info(f"Button clicked: {query.data}")

        if query.data == 'login':
            await self.login_handler.handle_login(update, context)

        elif query.data == 'set_target':
            await query.edit_message_text(text="Please send the target channel/group ID.")

        elif query.data == 'set_source':
            await query.edit_message_text(text="Please send the source channel/group IDs separated by commas.")

        elif query.data == 'run':
            await query.edit_message_text(text="Auto-forwarding started.")

        elif query.data == 'close':
            await query.edit_message_text(text="Auto-forward setup closed.")

    async def forward_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forward messages from source to target"""
        if not self.login_handler.is_logged_in:
            await update.message.reply_text("Please login first.")
            return

        if not self.target_channel:
            await update.message.reply_text("Target channel/group not set.")
            return

        if not self.source_channels:
            await update.message.reply_text("Source channels/groups not set.")
            return

        # Implement message forwarding logic here

def setup_handlers(application, config, db):
    autoforward_handler = AutoForwardHandler(config, db)
    application.add_handler(CommandHandler("autoforward", autoforward_handler.handle_autoforward_command))
    application.add_handler(CallbackQueryHandler(autoforward_handler.button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, autoforward_handler.login_handler.check_phone))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, autoforward_handler.login_handler.check_code))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, autoforward_handler.login_handler.check_password))
