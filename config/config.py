from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self, db):
        self.db = db
        self.config_collection = db['bot_config']
        self._load_config()
    
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
                    'api_url': 'https://example.com/api'
                }
            }
            self.config_collection.insert_one(default_config)
            self.config = default_config
        else:
            self.config = config
    
    def get(self, key, default=None):
        """Get config value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set config value"""
        self.config[key] = value
        self.config_collection.update_one(
            {'_id': 'bot_config'},
            {'$set': {key: value}},
            upsert=True
        ) 