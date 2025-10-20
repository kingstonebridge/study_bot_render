import os
import asyncio
import logging
from threading import Thread
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8295704989:AAHTc5Vr9_7aCz_FJuGKqqgbl9vQYx2Awk8')
BOT_USERNAME = "StudyGeniusProBot"  # Your actual bot username
# === END CONFIGURATION ===

# Setup detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed to DEBUG for more info
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class StudyBot:
    def __init__(self):
        logger.info("🤖 Initializing Study Bot...")
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            logger.info("✅ Application created successfully")
            self.setup_handlers()
            logger.info("✅ Handlers setup completed")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info("🔄 Handlers registered: start, help, test, message")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"🎯 /start command received from {user.first_name} (ID: {user.id})")
        
        welcome_text = f"""
🤖 **Hello {user.first_name}! Welcome to Study Helper Pro!** 🎓

I'm your AI study assistant ready to help you:

📚 **Organize your subjects**
🔔 **Set study reminders** 
📊 **Track your progress**
🎯 **Create study plans**

Try these commands:
• `/start` - Show this welcome message
• `/help` - Get help and instructions
• `add mathematics` - Add a subject
• `subjects` - List your subjects

Or just use the buttons below! 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Add Subject", callback_data="add_subject")],
            [InlineKeyboardButton("🔔 Set Reminder", callback_data="set_reminder")],
            [InlineKeyboardButton("📊 View Stats", callback_data="view_stats")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            logger.info("✅ Welcome message sent successfully")
        except Exception as e:
            logger.error(f"❌ Failed to send welcome message: {e}")
            await update.message.reply_text("Welcome! There was an error loading the menu. Please try /help")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        logger.info("🆘 /help command received")
        
        help_text = """
❓ **Study Helper Pro - Help Guide**

🎯 **Available Commands:**
• `/start` - Start the bot and show menu
• `/help` - Show this help message  
• `/test` - Test if bot is working

📚 **Subject Management:**
• `add mathematics` - Add a subject
• `remove mathematics` - Remove a subject
• `subjects` - List your subjects

🔔 **Study Tools:**
• `remind study math 18:00` - Set reminder
• `timer 25` - Start study timer
• `progress math 2` - Log study time

💡 **Tip:** Use the buttons for easy navigation!

**Bot is currently in testing mode. More features coming soon!** 🚀
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        logger.info("✅ Help message sent")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        logger.info("🧪 /test command received")
        
        await update.message.reply_text("✅ **Bot is working!** 🎉\n\nYour Study Helper Pro bot is active and responding correctly!")
        logger.info("✅ Test message sent")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        user_message = update.message.text
        user = update.effective_user
        
        logger.info(f"📨 Message from {user.first_name}: {user_message}")
        
        # Simple responses for testing
        if user_message.lower().startswith('add '):
            subject = user_message[4:].strip()
            response = f"✅ **Subject '{subject}' added!** 📚\n\nThis is a demo. In full version, I'll remember your subjects!"
        
        elif user_message.lower() == 'subjects':
            response = "📚 **Your Subjects:**\n\n• Mathematics (demo)\n• Physics (demo)\n\n*Demo mode - real tracking coming soon!*"
        
        elif user_message.lower().startswith('remove '):
            subject = user_message[7:].strip()
            response = f"🗑️ **Subject '{subject}' removed!**\n\n*Demo mode - real functionality coming soon!*"
        
        else:
            response = "🤖 **I received your message!**\n\nTry:\n• `/start` for main menu\n• `/help` for instructions\n• `add mathematics` to test subject adding\n\n*Bot in testing phase* 🚧"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        logger.info(f"✅ Response sent to {user.first_name}")
    
    async def setup_webhook(self):
        """Setup webhook for production"""
        try:
            if BOT_TOKEN.startswith('YOUR_') or 'EXAMPLE' in BOT_TOKEN:
                logger.error("❌ INVALID BOT TOKEN - Please set real BOT_TOKEN")
                return False
                
            webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL', '')}/webhook"
            if webhook_url.startswith('https:///'):
                logger.warning("🌐 No RENDER_EXTERNAL_URL, using polling")
                return False
            
            await self.application.bot.set_webhook(webhook_url)
            logger.info(f"✅ Webhook set: {webhook_url}")
            
            # Test bot connection
            bot_info = await self.application.bot.get_me()
            logger.info(f"🤖 Bot connected: @{bot_info.username} - {bot_info.first_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Webhook setup failed: {e}")
            return False

# Initialize bot
study_bot = StudyBot()

@app.route('/')
def home():
    bot_link = f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME != "StudyGeniusProBot" else "#"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Helper Pro - Debug</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4CAF50; color: white; padding: 40px; border-radius: 10px; text-align: center; }}
            .status {{ background: #ffeb3b; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .btn {{ background: #2196F3; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔧 Study Helper Pro - Debug Mode</h1>
            <p>Testing and Debugging Interface</p>
        </div>
        
        <div class="status">
            <h3>🚦 Status Check</h3>
            <p><strong>Bot Token:</strong> {"✅ Set" if not BOT_TOKEN.startswith('YOUR_') else "❌ NOT SET"}</p>
            <p><strong>Bot Username:</strong> @{BOT_USERNAME}</p>
            <p><strong>Environment:</strong> {os.environ.get('RENDER', 'Development')}</p>
        </div>
        
        <div style="text-align: center;">
            <h3>🧪 Test Your Bot</h3>
            <p>Click below to open your bot and send <code>/start</code></p>
            <a href="{bot_link}" class="btn">🚀 Open My Bot</a>
            <a href="/logs" class="btn">📊 View Logs</a>
        </div>
        
        <div style="margin-top: 30px;">
            <h3>🔧 Troubleshooting Steps:</h3>
            <ol>
                <li>Click "Open My Bot" above</li>
                <li>Send <code>/start</code> to your bot</li>
                <li>If nothing happens, check the logs</li>
                <li>Verify BOT_TOKEN in Render environment variables</li>
            </ol>
        </div>
    </body>
    </html>
    '''

@app.route('/logs')
def show_logs():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Logs</title>
        <style>
            body {{ font-family: monospace; margin: 20px; }}
            .log {{ background: #f5f5f5; padding: 10px; border-left: 4px solid #4CAF50; }}
        </style>
    </head>
    <body>
        <h2>📊 Bot Logs</h2>
        <div class="log">
            <p>Logs will appear here when bot receives messages...</p>
            <p>Check your Render dashboard logs for detailed information.</p>
        </div>
        <p><a href="/">← Back to Debug Page</a></p>
    </body>
    </html>
    '''

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        logger.info("📥 Webhook received - Processing update...")
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, study_bot.application.bot)
        
        asyncio.run(study_bot.application.process_update(update))
        logger.info("✅ Webhook processed successfully")
        return 'ok'
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return 'error', 500

@app.route('/health')
def health_check():
    return {'status': 'running', 'bot': 'Study Helper Pro', 'mode': 'debug'}, 200

def run_flask():
    """Run Flask server"""
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False, use_reloader=False)

async def main():
    """Main application entry point"""
    logger.info("🚀 Starting Study Helper Pro Bot...")
    
    # Try webhook first
    if await study_bot.setup_webhook():
        logger.info("🌐 Running in WEBHOOK mode")
    else:
        logger.info("🔄 Running in POLLING mode")
        try:
            await study_bot.application.run_polling()
        except Exception as e:
            logger.error(f"❌ Polling failed: {e}")

if __name__ == '__main__':
    # Start Flask in background
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot
    asyncio.run(main())
    
