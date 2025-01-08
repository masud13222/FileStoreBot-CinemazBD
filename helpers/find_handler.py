from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import os
import re
from typing import List, Dict
from fuzzywuzzy import fuzz

class FindHandler:
    def __init__(self, config):
        self.config = config
        self.db = config.db
        self.files_collection = self.db['files']
        self.batches_collection = self.db['batches']
        self.search_results = {}  # Store search results per user
        self.ITEMS_PER_PAGE = 5
        
    def register_handlers(self, application):
        """Register callback query handler"""
        application.add_handler(CallbackQueryHandler(self.handle_pagination, pattern=r'^find_'))
        
    async def handle_find_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /find command to search files"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide what to search!\n\n"
                "Example:\n"
                "/find avengers\n"
                "/find spider man"
            )
            return
            
        search_text = ' '.join(context.args).lower()
        user_id = update.effective_user.id
        
        # Create regex pattern for search
        pattern = '.*'.join(re.escape(word) for word in search_text.split())
        regex = re.compile(pattern, re.IGNORECASE)
        
        # Search in files collection with fuzzy matching
        files = []
        for file in self.files_collection.find():
            file_name = file.get('file_name', '') or ''
            caption = file.get('caption', '') or ''
            
            # Check for fuzzy matches
            name_ratio = fuzz.partial_ratio(search_text, file_name.lower())
            caption_ratio = fuzz.partial_ratio(search_text, caption.lower())
            
            if name_ratio > 70 or caption_ratio > 70:  # 70% similarity threshold
                file['match_score'] = max(name_ratio, caption_ratio)
                files.append(file)
        
        # Sort files by match score
        files.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Search in batches with fuzzy matching
        batches = []
        for batch in self.batches_collection.find():
            matching_files = []
            for f in batch.get('files', []):
                file_name = f.get('file_name', '') or ''
                caption = f.get('caption', '') or ''
                
                name_ratio = fuzz.partial_ratio(search_text, file_name.lower())
                caption_ratio = fuzz.partial_ratio(search_text, caption.lower())
                
                if name_ratio > 70 or caption_ratio > 70:
                    f['match_score'] = max(name_ratio, caption_ratio)
                    matching_files.append(f)
            
            if matching_files:
                batch['matching_files'] = sorted(matching_files, key=lambda x: x.get('match_score', 0), reverse=True)
                batch['match_score'] = max(f.get('match_score', 0) for f in matching_files)
                batches.append(batch)
        
        # Sort batches by best match score
        batches.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        if not files and not batches:
            await update.message.reply_text(
                f"❌ No files found matching: {search_text}"
            )
            return
            
        # Store search results for pagination
        self.search_results[user_id] = {
            'query': search_text,
            'files': files,
            'batches': batches,
            'page': 0,
            'view_mode': 'all'  # Default view mode
        }
        
        # Show first page
        await self.show_page(update.message, user_id)
        
    async def show_page(self, message, user_id: int):
        """Show a page of search results"""
        results = self.search_results.get(user_id)
        if not results:
            return
            
        page = results['page']
        view_mode = results.get('view_mode', 'all')
        
        # Filter results based on view mode
        if view_mode == 'single':
            files = results['files']
            batches = []
        elif view_mode == 'batch':
            files = []
            batches = results['batches']
        else:  # 'all'
            files = results['files']
            batches = results['batches']
            
        total_items = len(files) + len(batches)
        total_pages = (total_items + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        
        start_idx = page * self.ITEMS_PER_PAGE
        end_idx = start_idx + self.ITEMS_PER_PAGE
        
        # Generate response for current page
        response = f"🔍 <b>Search Results</b>\n"
        response += f"└ Query: <code>{results['query']}</code>\n\n"
        response += f"📊 <b>Stats</b>\n"
        response += f"├ Total Files: {len(results['files'])}\n"
        response += f"├ Total Batches: {len(results['batches'])}\n"
        response += f"└ Page: {page + 1}/{total_pages}\n\n"
        
        worker_url = os.getenv('WORKER_URL', '').rstrip('/')
        current_idx = 0
        
        # Add files
        if files:
            response += "📁 <b>Single Files</b>\n"
            for file in files:
                if current_idx >= start_idx and current_idx < end_idx:
                    file_name = file.get('file_name', 'No name')
                    caption = file.get('caption', '')
                    file_code = file.get('file_code', '')
                    file_type = file.get('file_type', 'file').upper()
                    match_score = file.get('match_score', 0)
                    
                    # Get file size if available
                    size = ""
                    if 'file_size' in file:
                        size_mb = file['file_size'] / (1024 * 1024)
                        if size_mb >= 1024:
                            size = f"[{size_mb/1024:.1f}GB]"
                        else:
                            size = f"[{size_mb:.1f}MB]"
                    
                    link = f"{worker_url}/{file_code}"
                    
                    response += f"\n{current_idx + 1}. <b>{file_type}</b> {size} ({match_score}% match)\n"
                    response += f"├ Name: <code>{file_name}</code>\n"
                    if caption and caption != file_name:
                        response += f"└ Link: {link}\n"
                    else:
                        response += f"└ Link: {link}\n"
                current_idx += 1
                if current_idx >= end_idx:
                    break
                    
        # Add batches
        if batches and current_idx < end_idx:
            if files:
                response += "\n"  # Add space between files and batches
            response += "📚 <b>Batches</b>\n"
            for batch in batches:
                if current_idx >= start_idx and current_idx < end_idx:
                    batch_code = batch.get('batch_code', '')
                    batch_link = f"{worker_url}/batch_{batch_code}"
                    matching_files = batch.get('matching_files', [])
                    match_score = batch.get('match_score', 0)
                    
                    response += f"\n{current_idx + 1}. <b>Batch</b> [{len(matching_files)} files] ({match_score}% match)\n"
                    response += f"├ Link: {batch_link}\n"
                    
                    # Show first 3 matching files as preview
                    if matching_files:
                        response += "└ Preview:\n"
                        for idx, file in enumerate(matching_files[:3], 1):
                            file_name = file.get('file_name', 'No name')
                            file_match = file.get('match_score', 0)
                            response += f"   {idx}. <code>{file_name}</code> ({file_match}% match)\n"
                        
                        if len(matching_files) > 3:
                            response += f"      ↳ ...and {len(matching_files) - 3} more files\n"
                current_idx += 1
                if current_idx >= end_idx:
                    break
        
        # Create keyboard with filter and navigation buttons
        keyboard = []
        
        # Filter buttons
        filter_row = []
        for mode in [('🔄 All', 'all'), ('📄 Files', 'single'), ('📚 Batch', 'batch')]:
            callback_data = f"find_filter_{user_id}_{mode[1]}"
            is_active = view_mode == mode[1]
            text = f"✅ {mode[0]}" if is_active else mode[0]
            filter_row.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(filter_row)
        
        # Navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"find_prev_{user_id}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="ignore"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"find_next_{user_id}"))
        if nav_row:
            keyboard.append(nav_row)
            
        # Close button
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data=f"find_close_{user_id}")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Try to edit existing message
            await message.edit_text(response, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
        except Exception as e:
            try:
                # If can't edit, send new message
                await message.reply_text(response, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                # If HTML parsing fails, try without formatting
                await message.reply_text("❌ Error formatting message. Please try again.")
            
    async def handle_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pagination button clicks"""
        query = update.callback_query
        data = query.data
        user_id = int(data.split('_')[2])
        
        if user_id != query.from_user.id:
            await query.answer("This is not your search result!", show_alert=True)
            return
            
        results = self.search_results.get(user_id)
        if not results:
            await query.answer("Search results expired. Please search again.", show_alert=True)
            return
            
        if data.startswith('find_prev_'):
            results['page'] = max(0, results['page'] - 1)
        elif data.startswith('find_next_'):
            total_items = len(results['files']) + len(results['batches'])
            total_pages = (total_items + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
            results['page'] = min(total_pages - 1, results['page'] + 1)
        elif data.startswith('find_filter_'):
            view_mode = data.split('_')[3]
            results['view_mode'] = view_mode
            results['page'] = 0  # Reset to first page
        elif data.startswith('find_close_'):
            await query.message.delete()
            return
            
        await query.answer()
        await self.show_page(query.message, user_id) 