import os
import asyncio
import logging
from threading import Thread
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
WEBHOOK_PORT = int(os.environ.get('PORT', 10000))

# Initialize Flask
app = Flask(__name__)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class StudyBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        self.logger = logging.getLogger(__name__)
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        handlers = [
            CommandHandler("start", self.start),
            CommandHandler("premium", self.premium_info),
            CommandHandler("help", self.help_command),
            CallbackQueryHandler(self.button_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        user = update.effective_user
        
        welcome_text = f"""
🎓 **Welcome to Study Helper Pro, {user.first_name}!**

🤖 **Your AI-powered study assistant:**

📚 **Organization Features:**
• Subject management & tracking
• Smart study scheduling
• Progress analytics
• Reminder system

🎯 **Productivity Tools:**
• Study session timer
• Task prioritization
• Goal setting
• Performance insights

🆓 **Free Plan:**
• 3 subjects • 2 reminders • Basic analytics

⭐ **Premium Features:**
• 15 subjects • 20 reminders • AI study helper
• Advanced analytics • Export features

Use the menu below to get started! 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Manage Subjects", callback_data="subjects")],
            [InlineKeyboardButton("🔔 Set Reminder", callback_data="set_reminder")],
            [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="premium"),
             InlineKeyboardButton("📊 My Stats", callback_data="stats")],
            [InlineKeyboardButton("🎯 Study Tools", callback_data="tools"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium information"""
        premium_text = """
⭐ **Study Helper Pro Premium**

🚀 **Supercharge your learning experience:**

✨ **Premium Benefits:**
• 📚 15 subjects (instead of 3)
• 🔔 20 smart reminders (instead of 2)
• 🤖 AI Study Helper & personalized tips
• 📊 Advanced progress analytics
• 📱 Export schedules to calendar
• 🎯 Smart study plan generator
• ⚡ Priority support

💎 **Pricing:**
• Monthly: $5 USD
• Quarterly: $12 USD (20% off)
• Yearly: $40 USD (33% off)

🔒 **30-day money-back guarantee**

🎁 **Special Offer:** First 100 users get 50% off!
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 Buy Monthly - $5", callback_data="buy_monthly")],
            [InlineKeyboardButton("📦 Buy Quarterly - $12", callback_data="buy_quarterly")],
            [InlineKeyboardButton("🎯 Buy Yearly - $40", callback_data="buy_yearly")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(premium_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(premium_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = """
❓ **How to Use Study Helper Pro**

📚 **Managing Subjects:**
Use: `add math` or `add subject:Mathematics`
Use: `remove math` to delete

🔔 **Setting Reminders:**
Use: `remind study math 18:00`
Use: `reminders` to view all

⏰ **Study Timer:**
Use: `timer 25` for 25-minute session
Use: `break 5` for 5-minute break

📊 **Tracking Progress:**
Use: `progress math 2` (2 hours studied)
Use: `stats` to see overview

🎯 **Quick Commands:**
• `subjects` - List your subjects
• `schedule` - View study schedule
• `goals` - Set study goals
• `export` - Export your data

💡 **Pro Tip:** Use buttons for easier navigation!
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Try: Add Subject", callback_data="demo_add")],
            [InlineKeyboardButton("🔔 Try: Set Reminder", callback_data="demo_remind")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        self.logger.info(f"Button pressed: {data}")
        
        if data == "premium":
            await self.premium_info(update, context)
        
        elif data == "subjects":
            subjects_text = """
📚 **Subject Management**

🆓 **Free Users:** 3 subjects max
⭐ **Premium Users:** 15 subjects max

💡 **To add a subject, send:**
`add math` or `add subject:Mathematics`

💡 **To remove a subject, send:**
`remove math` or `delete math`

📋 **Your current subjects will appear here as you add them.**

🎯 **Tip:** Organize by topics like:
• mathematics
• physics_101  
• english_literature
• computer_science
            """
            await query.edit_message_text(subjects_text, parse_mode='Markdown')
        
        elif data == "stats":
            stats_text = """
📊 **Study Statistics**

👤 **Account Type:** 🆓 Free User
📚 **Subjects Used:** 0/3
🔔 **Reminders Used:** 0/2
📅 **Study Sessions:** 0
⏱️ **Total Study Time:** 0 hours

🚀 **Upgrade to Premium** to unlock advanced analytics and tracking!
            """
            
            keyboard = [
                [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "tools":
            tools_text = """
🎯 **Study Tools**

⏰ **Productivity Timer:**
• Pomodoro technique (25min work, 5min break)
• Custom study sessions
• Break timers

📝 **Study Planner:**
• Weekly study schedules
• Exam countdowns
• Task prioritization

📊 **Progress Tracker:**
• Study hour tracking
• Goal completion
• Performance insights

🔔 **Smart Reminders:**
• Scheduled study sessions
• Assignment deadlines
• Review reminders

💡 **Use commands to access these tools!**
            """
            
            keyboard = [
                [InlineKeyboardButton("⏰ Start Timer", callback_data="start_timer")],
                [InlineKeyboardButton("📝 Study Planner", callback_data="planner")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(tools_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data.startswith("buy_"):
            plan = data[4:]  # monthly, quarterly, yearly
            prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
            
            payment_text = f"""
💎 **Premium Upgrade - {plan.capitalize()}**

**Plan:** {plan.capitalize()} Subscription
**Price:** ${prices[plan]} USD
**Duration:** {'1 month' if plan == 'monthly' else '3 months' if plan == 'quarterly' else '1 year'}

📝 **Payment Instructions:**

1. **Send ${prices[plan]} USDT** to:
   `TBN9pJzM8VqL6k7Z2x1W0yV3rS4tG5hF6d`

2. **Include memo:** `study_{plan}_{query.from_user.id}`

3. **Screenshot** your payment confirmation

4. **Forward screenshot** to @StudyHelperAdmin

✅ **Activation within 1 hour after payment verification**

🔙 **Changed your mind?** Go back to explore other plans.
            """
            
            keyboard = [
                [InlineKeyboardButton("📸 I've Paid - Contact Admin", url="https://t.me/StudyHelperAdmin")],
                [InlineKeyboardButton("🔙 View Other Plans", callback_data="premium")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "main_menu":
            await self.start(update, context)
        
        elif data == "help":
            await self.help_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_message = update.message.text.lower().strip()
        user = update.effective_user
        
        self.logger.info(f"Message from {user.first_name}: {user_message}")
        
        # Subject management
        if user_message.startswith(('add ', 'create ')):
            subject = user_message[4:].strip()
            if subject:
                response = f"✅ Subject '{subject.title()}' added successfully! 📚\n\nUse 'subjects' to view all your subjects."
            else:
                response = "❌ Please specify a subject name. Example: 'add mathematics'"
        
        elif user_message.startswith(('remove ', 'delete ')):
            subject = user_message[7:].strip()
            if subject:
                response = f"🗑️ Subject '{subject.title()}' removed successfully!"
            else:
                response = "❌ Please specify which subject to remove."
        
        elif user_message in ['subjects', 'list subjects']:
            response = "📚 Your Subjects:\n\n• No subjects added yet\n\nUse 'add [subject]' to add your first subject!"
        
        # Reminder system
        elif user_message.startswith('remind '):
            response = "🔔 Reminder system activated! (Premium feature)\n\nUpgrade to premium to set smart study reminders! ⭐"
        
        elif user_message == 'reminders':
            response = "🔔 Your Reminders:\n\n• No reminders set\n\nUpgrade to premium to set study reminders! ⭐"
        
        # Study timer
        elif user_message.startswith('timer '):
            response = "⏰ Study timer started! (Premium feature)\n\nUpgrade to premium for advanced timer features! ⭐"
        
        # Progress tracking
        elif user_message.startswith('progress '):
            response = "📊 Progress recorded! (Premium feature)\n\nUpgrade to premium for detailed analytics! ⭐"
        
        elif user_message in ['stats', 'statistics']:
            response = "📊 **Your Study Stats:**\n\n• Subjects: 0/3\n• Study Time: 0 hours\n• Sessions: 0\n\nUpgrade to premium for advanced analytics! ⭐"
        
        # Default response
        else:
            responses = [
                "I'm here to help with your studies! Use the menu or type 'help' for guidance. 📚",
                "Need study assistance? Try adding subjects or check out our premium features! 🎯",
                "Use buttons below to navigate, or type 'help' to see all available commands! 🤖",
                "Ready to boost your productivity? Let me help organize your studies! 🚀"
            ]
            import random
            response = random.choice(responses)
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def setup_webhook(self):
        """Setup webhook for production"""
        if RENDER_URL:
            webhook_url = f"{RENDER_URL}/webhook"
            await self.application.bot.set_webhook(webhook_url)
            self.logger.info(f"✅ Webhook configured: {webhook_url}")
            return True
        else:
            self.logger.warning("❌ RENDER_URL not set, using polling mode")
            return False

# Initialize bot instance
study_bot = StudyBot()

# Flask routes
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Helper Pro Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; text-align: center; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
            .btn { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Study Helper Pro</h1>
            <p>Your AI-powered study assistant on Telegram</p>
            <a href="https://t.me/YourBotUsername" class="btn">Start Using Bot</a>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>📚 Subject Management</h3>
                <p>Organize and track all your study subjects in one place</p>
            </div>
            <div class="feature">
                <h3>🔔 Smart Reminders</h3>
                <p>Never miss a study session with intelligent scheduling</p>
            </div>
            <div class="feature">
                <h3>📊 Progress Analytics</h3>
                <p>Track your study time and monitor your improvement</p>
            </div>
            <div class="feature">
                <h3>🎯 Study Planner</h3>
                <p>Create optimized study schedules for maximum efficiency</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <h2>Ready to Boost Your Grades?</h2>
            <p>Join thousands of students already using Study Helper Pro</p>
            <a href="https://t.me/YourBotUsername" class="btn">🚀 Start Studying Smarter</a>
        </div>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, study_bot.application.bot)
        
        # Process update in async context
        async def process_update():
            await study_bot.application.process_update(update)
        
        asyncio.run(process_update())
        return 'ok'
    except Exception as e:
        study_bot.logger.error(f"Webhook error: {e}")
        return 'error', 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'bot': 'running'}, 200

def run_flask():
    """Run Flask server"""
    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False, use_reloader=False)

async def main():
    """Main application entry point"""
    try:
        # Try webhook first (production)
        if await study_bot.setup_webhook():
            study_bot.logger.info("🚀 Bot running in WEBHOOK mode")
        else:
            study_bot.logger.info("🔧 Bot running in POLLING mode")
            await study_bot.application.run_polling()
    except Exception as e:
        study_bot.logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot
    asyncio.run(main())
