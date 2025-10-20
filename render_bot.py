import os
import asyncio
import logging
from threading import Thread
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === CONFIGURATION - UPDATE THESE ===
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8295704989:AAHTc5Vr9_7aCz_FJuGKqqgbl9vQYx2Awk8')
BOT_USERNAME = "StudyGeniusProBot"  # Like @StudyGeniusProBot
ADMIN_USERNAME = "@Kingstonebridge"  # Your Telegram @username
# === END CONFIGURATION ===

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
WEBHOOK_PORT = int(os.environ.get('PORT', 10000))

# Initialize Flask
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StudyBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("premium", self.premium_info))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
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

Click below to upgrade! 🚀
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
        
        if data == "premium":
            await self.premium_info(update, context)
        
        elif data == "subjects":
            subjects_text = """
📚 **Subject Management**

🆓 **Free Users:** 3 subjects max
⭐ **Premium Users:** 15 subjects max

💡 **To add a subject, send:**
`add math` or `add subject:Mathematics`

📋 **Your current subjects will appear here as you add them.**
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

🚀 **Upgrade to Premium** to unlock advanced analytics!
            """
            
            keyboard = [
                [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data.startswith("buy_"):
            plan = data[4:]
            prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
            
            payment_text = f"""
💎 **Premium Upgrade - {plan.capitalize()}**

**Plan:** {plan.capitalize()} Subscription
**Price:** ${prices[plan]} USD

📝 **Payment Instructions:**

1. **Contact {ADMIN_USERNAME}** for payment details
2. **Mention:** "I want {plan} premium"
3. **You'll receive** payment instructions
4. **Activation within 1 hour** after payment

✅ **Start studying smarter with premium features!**
            """
            
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔙 View Plans", callback_data="premium")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "main_menu":
            await self.start(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_message = update.message.text.lower().strip()
        
        if user_message.startswith(('add ', 'create ')):
            subject = user_message[4:].strip()
            response = f"✅ Subject '{subject.title()}' added successfully! 📚"
        
        elif user_message.startswith(('remove ', 'delete ')):
            subject = user_message[7:].strip()
            response = f"🗑️ Subject '{subject.title()}' removed successfully!"
        
        elif user_message in ['subjects', 'list subjects']:
            response = "📚 Your Subjects:\n\n• No subjects added yet\n\nUse 'add [subject]' to add your first subject!"
        
        else:
            responses = [
                "I'm here to help with your studies! Use the menu or type 'help' for guidance. 📚",
                "Need study assistance? Try adding subjects or check out premium features! 🎯"
            ]
            import random
            response = random.choice(responses)
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def setup_webhook(self):
        """Setup webhook for production"""
        if RENDER_URL:
            webhook_url = f"{RENDER_URL}/webhook"
            await self.application.bot.set_webhook(webhook_url)
            logger.info(f"✅ Webhook configured: {webhook_url}")
            return True
        return False

# Initialize bot
study_bot = StudyBot()

# === UPDATED HTML WITH YOUR ACTUAL BOT LINK ===
@app.route('/')
def home():
    your_bot_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}" if BOT_USERNAME != "YOUR_ACTUAL_BOT_USERNAME" else "#"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Helper Pro Bot</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; text-align: center; }}
            .btn {{ display: inline-block; background: #25D366; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 10px; font-size: 18px; }}
            .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
            .feature {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Study Helper Pro</h1>
            <p>Your AI-powered study assistant on Telegram</p>
            <a href="{your_bot_link}" class="btn">🚀 Start Using OUR Bot</a>
            <p><small>Direct link to YOUR unique bot</small></p>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>📚 Subject Management</h3>
                <p>Organize and track all your study subjects</p>
            </div>
            <div class="feature">
                <h3>🔔 Smart Reminders</h3>
                <p>Never miss a study session</p>
            </div>
            <div class="feature">
                <h3>📊 Progress Analytics</h3>
                <p>Track your study time and improvement</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <h2>Ready to Boost Your Grades?</h2>
            <a href="{your_bot_link}" class="btn">🎯 Start Studying Smarter</a>
        </div>
    </body>
    </html>
    '''

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, study_bot.application.bot)
        asyncio.run(study_bot.application.process_update(update))
        return 'ok'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'error', 500

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'bot': 'running'}, 200

def run_flask():
    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False, use_reloader=False)

async def main():
    if await study_bot.setup_webhook():
        logger.info("🚀 Bot running in WEBHOOK mode")
    else:
        logger.info("🔧 Bot running in POLLING mode")
        await study_bot.application.run_polling()

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(main())
