from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import psutil
import os
import time
from datetime import datetime

class StatsHandler:
    def __init__(self, config):
        self.config = config
        self.db = config.db
        self.files_collection = self.db['files']
        self.batches_collection = self.db['batches']
        self.start_time = time.time()
        
    def register_handlers(self, application):
        """Register callback query handler"""
        application.add_handler(CallbackQueryHandler(self.handle_callback, pattern=r'^stats_'))
        
    async def handle_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        # Create main menu keyboard
        keyboard = [
            [
                InlineKeyboardButton("🖥️ Server Info", callback_data="stats_server"),
                InlineKeyboardButton("🤖 Bot Info", callback_data="stats_bot")
            ],
            [
                InlineKeyboardButton("💾 Database", callback_data="stats_db"),
                InlineKeyboardButton("❌ Close", callback_data="stats_close")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 <b>Bot Statistics</b>\n"
            "Choose a category to view details:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        data = query.data
        
        if data == "stats_close":
            await query.message.delete()
            return
            
        if data == "stats_server":
            await self.show_server_info(query)
        elif data == "stats_bot":
            await self.show_bot_info(query)
        elif data == "stats_db":
            await self.show_database_menu(query)
        elif data == "stats_db_clean_all":
            await self.clean_database(query, clean_type="all")
        elif data == "stats_db_clean_single":
            await self.clean_database(query, clean_type="single")
        elif data == "stats_db_clean_batch":
            await self.clean_database(query, clean_type="batch")
        elif data == "stats_back":
            await self.show_main_menu(query)
            
        await query.answer()
        
    async def show_main_menu(self, query):
        """Show main stats menu"""
        keyboard = [
            [
                InlineKeyboardButton("🖥️ Server Info", callback_data="stats_server"),
                InlineKeyboardButton("🤖 Bot Info", callback_data="stats_bot")
            ],
            [
                InlineKeyboardButton("💾 Database", callback_data="stats_db"),
                InlineKeyboardButton("❌ Close", callback_data="stats_close")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "📊 <b>Bot Statistics</b>\n"
            "Choose a category to view details:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    async def show_server_info(self, query):
        """Show server information"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        uptime = time.time() - self.start_time
        days = int(uptime // (24 * 3600))
        hours = int((uptime % (24 * 3600)) // 3600)
        minutes = int((uptime % 3600) // 60)
        
        response = (
            "🖥️ <b>Server Information</b>\n\n"
            f"CPU Usage: {cpu_percent}%\n"
            f"RAM Usage: {memory.percent}%\n"
            f"Disk Usage: {disk.percent}%\n"
            f"Bot Uptime: {days}d {hours}h {minutes}m\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="stats_back")],
            [InlineKeyboardButton("❌ Close", callback_data="stats_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(response, reply_markup=reply_markup, parse_mode='HTML')
        
    async def show_bot_info(self, query):
        """Show bot statistics"""
        total_files = self.files_collection.count_documents({})
        total_batches = self.batches_collection.count_documents({})
        
        response = (
            "🤖 <b>Bot Statistics</b>\n\n"
            f"📁 Total Single Files: {total_files:,}\n"
            f"📚 Total Batches: {total_batches:,}\n"
            f"🔄 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="stats_back")],
            [InlineKeyboardButton("❌ Close", callback_data="stats_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(response, reply_markup=reply_markup, parse_mode='HTML')
        
    async def show_database_menu(self, query):
        """Show database management menu"""
        total_files = self.files_collection.count_documents({})
        total_batches = self.batches_collection.count_documents({})
        
        # Get database stats
        db_stats = self.db.command("dbStats")
        storage_size = db_stats["storageSize"] / (1024 * 1024)  # Convert to MB
        data_size = db_stats["dataSize"] / (1024 * 1024)  # Convert to MB
        
        response = (
            "💾 <b>Database Management</b>\n\n"
            f"📊 <b>Collections</b>\n"
            f"├ Single Files: {total_files:,}\n"
            f"└ Batches: {total_batches:,}\n\n"
            f"📦 <b>Storage Info</b>\n"
            f"├ Database: <code>{self.db.name}</code>\n"
            f"├ Storage Size: {storage_size:.2f} MB\n"
            f"└ Data Size: {data_size:.2f} MB\n\n"
            "⚠️ <b>Warning</b>: Cleaning operations cannot be undone!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🧹 Clean All", callback_data="stats_db_clean_all"),
            ],
            [
                InlineKeyboardButton("📄 Clean Singles", callback_data="stats_db_clean_single"),
                InlineKeyboardButton("📚 Clean Batches", callback_data="stats_db_clean_batch")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="stats_back")],
            [InlineKeyboardButton("❌ Close", callback_data="stats_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(response, reply_markup=reply_markup, parse_mode='HTML')
        
    async def clean_database(self, query, clean_type: str):
        """Clean database based on type"""
        if clean_type == "all":
            self.files_collection.delete_many({})
            self.batches_collection.delete_many({})
            message = "🧹 Cleaned all files and batches from database!"
        elif clean_type == "single":
            self.files_collection.delete_many({})
            message = "🧹 Cleaned all single files from database!"
        else:  # batch
            self.batches_collection.delete_many({})
            message = "🧹 Cleaned all batches from database!"
            
        # Show confirmation
        await query.answer(message, show_alert=True)
        
        # Return to database menu
        await self.show_database_menu(query) 