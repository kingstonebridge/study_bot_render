import os

# Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7543007145:AAG2WvycK864t6mp21eHBvkvVLoQbq6iw0M')

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///study_bot.db')

# Payment Configuration
PREMIUM_PRICES = {
    'monthly': 5.0,
    'quarterly': 12.0,
    'yearly': 40.0
}

# Feature Limits
MAX_FREE_SUBJECTS = 3
MAX_PREMIUM_SUBJECTS = 15
MAX_FREE_REMINDERS = 2
MAX_PREMIUM_REMINDERS = 20

# Admin Configuration
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '@StudyHelperAdmin')
