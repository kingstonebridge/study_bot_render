import os
import asyncio
import logging
import json
import time
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set in environment!")
    exit(1)

BOT_USERNAME = os.environ.get('BOT_USERNAME', '@StudyHelperProAIBot')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_ID = os.environ.get('ADMIN_ID', '')
BINANCE_WALLET = os.environ.get('BINANCE_WALLET_ADDRESS', '')

print(f"🔧 Configuration Loaded:")
print(f"   BOT_TOKEN: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print(f"   BOT_USERNAME: {BOT_USERNAME}")
print(f"   ADMIN_USERNAME: {ADMIN_USERNAME}")
print(f"   ADMIN_ID: {ADMIN_ID}")
print(f"   BINANCE_WALLET: {'✅ Set' if BINANCE_WALLET else '❌ Missing'}")
# === END CONFIGURATION ===

# Setup detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler('bot_debug.log')  # Save to file
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== SIMPLIFIED SYSTEMS ====================
class PaymentSystem:
    def __init__(self):
        self.wallet_address = BINANCE_WALLET
        self.pending_payments = {}
        logger.info("💰 Payment system initialized")
    
    def create_payment(self, user_id, amount, plan_type, username):
        try:
            memo = f"STUDY{user_id}{int(time.time())}"
            payment_data = {
                'wallet_address': self.wallet_address,
                'amount': amount,
                'memo': memo,
                'user_id': user_id,
                'username': username,
                'plan_type': plan_type,
                'status': 'pending'
            }
            self.pending_payments[memo] = payment_data
            logger.info(f"💰 Payment created: {memo}")
            return payment_data
        except Exception as e:
            logger.error(f"❌ Payment error: {e}")
            return None

class Database:
    def __init__(self):
        self.users = {}
        logger.info("🗄️ Database initialized")
    
    def get_user(self, user_id):
        return self.users.get(str(user_id), {
            'user_id': user_id,
            'subjects': [],
            'is_premium': False,
            'study_time': 0
        })
    
    def save_user(self, user_id, user_data):
        self.users[str(user_id)] = user_data

# Initialize systems
payment_system = PaymentSystem()
database = Database()

# ==================== TELEGRAM BOT ====================
class StudyBot:
    def __init__(self):
        logger.info("🤖 Initializing Study Bot...")
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            logger.info("✅ Application created successfully")
            self.setup_handlers()
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            raise
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        logger.info("🔄 Setting up handlers...")
        
        # Basic commands first
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Then other handlers
        self.application.add_handler(CommandHandler("premium", self.premium_info))
        self.application.add_handler(CommandHandler("subjects", self.list_subjects))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("earnings", self.earnings_stats))
        self.application.add_handler(CommandHandler("confirm", self.confirm_payment))
        
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("✅ All handlers registered")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simple test command"""
        logger.info("🧪 Test command received")
        await update.message.reply_text("✅ **Bot is working!** 🎉\n\nSend `/start` to see the main menu.")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        user = update.effective_user
        logger.info(f"🎯 /start command from {user.first_name} (ID: {user.id})")
        
        welcome_text = f"""
🤖 **Hello {user.first_name}!** 

I'm Study Helper Pro - your AI study assistant!

🚀 **Quick Start:**
• Use buttons below for easy navigation
• Or type commands like `add mathematics`

📚 **Free Features:**
• 3 subjects • 2 reminders • Basic analytics

⭐ **Premium Features:**
• 15 subjects • 20 reminders • AI helper

**Choose an option below!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Add Subject", callback_data="add_subject")],
            [InlineKeyboardButton("⭐ Get Premium", callback_data="premium")],
            [InlineKeyboardButton("📊 My Stats", callback_data="stats"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        try:
            await update.message.reply_text(
                welcome_text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
            logger.info("✅ Welcome message sent successfully")
        except Exception as e:
            logger.error(f"❌ Failed to send welcome: {e}")
            await update.message.reply_text("Welcome! There was an error. Try /test")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        logger.info("🆘 Help command received")
        help_text = """
❓ **Help Guide**

**Commands:**
• `/start` - Main menu
• `/test` - Test if bot works
• `/premium` - Upgrade options
• `add mathematics` - Add subject

**Buttons work too!**
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium info"""
        logger.info("💎 Premium info requested")
        premium_text = """
⭐ **Premium Plans:**

• **Monthly:** $5
• **Quarterly:** $12  
• **Yearly:** $40

**Click a plan below!**
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 Monthly - $5", callback_data="buy_monthly")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        
        if update.message:
            await update.message.reply_text(premium_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(premium_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def list_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List subjects"""
        user_id = update.effective_user.id
        user_data = database.get_user(user_id)
        subjects = user_data.get('subjects', [])
        
        if not subjects:
            response = "📚 **No subjects yet!**\n\nUse `add mathematics` to add your first subject!"
        else:
            subject_list = "\n".join([f"• {s}" for s in subjects])
            response = f"📚 **Your Subjects:**\n\n{subject_list}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show stats"""
        user_id = update.effective_user.id
        user_data = database.get_user(user_id)
        
        stats_text = f"""
📊 **Your Stats:**

👤 **Account:** {'⭐ PREMIUM' if user_data.get('is_premium') else '🆓 FREE'}
📚 **Subjects:** {len(user_data.get('subjects', []))}
⏱️ **Study Time:** {user_data.get('study_time', 0)} hours

**Keep studying!** 📚
        """
        
        if update.message:
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(stats_text, parse_mode='Markdown')
    
    async def handle_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type):
        """Handle payment"""
        query = update.callback_query
        user = query.from_user
        
        prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
        amount = prices.get(plan_type, 5)
        
        payment_data = payment_system.create_payment(
            user.id, amount, plan_type, user.username or user.first_name
        )
        
        if payment_data:
            payment_text = f"""
💎 **{plan_type.capitalize()} Plan - ${amount}**

📍 **Send to:** 
`{payment_data['wallet_address']}`

📝 **Memo:** `{payment_data['memo']}`

🌐 **Network:** TRC20
        """
            
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 Back", callback_data="premium")]
            ]
            
            await query.edit_message_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Payment error. Contact admin.")
    
    async def earnings_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin earnings"""
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return
        
        earnings = len(payment_system.pending_payments)
        await update.message.reply_text(f"💰 {earnings} pending payments")
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin confirm payment"""
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return
        
        if context.args:
            memo = context.args[0]
            if memo in payment_system.pending_payments:
                payment_system.pending_payments[memo]['status'] = 'confirmed'
                await update.message.reply_text(f"✅ Payment {memo} confirmed!")
            else:
                await update.message.reply_text("❌ Payment not found")
        else:
            await update.message.reply_text("Usage: /confirm MEMO")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buttons"""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        logger.info(f"🔘 Button pressed: {data}")
        
        if data == "premium":
            await self.premium_info(update, context)
        elif data.startswith("buy_"):
            plan = data[4:]
            await self.handle_payment(update, context, plan)
        elif data == "stats":
            await self.show_stats(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data == "main_menu":
            await self.start(update, context)
        elif data == "add_subject":
            await query.edit_message_text("📚 **Add a subject:**\n\nType: `add mathematics`")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages"""
        user_message = update.message.text.lower()
        user_id = update.effective_user.id
        
        logger.info(f"📨 Message: {user_message} from {user_id}")
        
        if user_message.startswith('add '):
            subject = user_message[4:].strip()
            user_data = database.get_user(user_id)
            if 'subjects' not in user_data:
                user_data['subjects'] = []
            user_data['subjects'].append(subject.title())
            database.save_user(user_id, user_data)
            response = f"✅ **'{subject.title()}' added!** 📚"
        elif user_message == 'subjects':
            user_data = database.get_user(user_id)
            subjects = user_data.get('subjects', [])
            if subjects:
                subject_list = "\n".join([f"• {s}" for s in subjects])
                response = f"📚 **Your Subjects:**\n\n{subject_list}"
            else:
                response = "📚 **No subjects yet!**\n\nUse `add mathematics`"
        else:
            response = "🤖 Try: `add mathematics` or use the buttons!"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def setup_webhook(self):
        """Setup webhook"""
        try:
            if os.environ.get('RENDER'):
                webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
                await self.application.bot.set_webhook(webhook_url)
                logger.info(f"✅ Webhook set: {webhook_url}")
                return True
        except Exception as e:
            logger.error(f"❌ Webhook failed: {e}")
        return False

# Initialize bot
study_bot = StudyBot()

# ==================== FLASK ROUTES ====================
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Helper Pro</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: #4CAF50; color: white; padding: 40px; border-radius: 10px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Study Helper Pro</h1>
            <p>Your AI study assistant on Telegram</p>
            <p><strong>Status: ✅ Bot is running</strong></p>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <p>Debug mode active - check Render logs for details</p>
        </div>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook"""
    try:
        logger.info("📥 Webhook received")
        json_data = request.get_json()
        logger.debug(f"Webhook data: {json_data}")
        
        update = Update.de_json(json_data, study_bot.application.bot)
        asyncio.run(study_bot.application.process_update(update))
        
        logger.info("✅ Webhook processed")
        return 'ok'
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return 'error', 500

@app.route('/test')
def test():
    return "✅ Flask server is working!"

def run_flask():
    """Run Flask"""
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False, use_reloader=False)

async def main():
    """Main entry point"""
    logger.info("🚀 Starting Study Bot...")
    
    # Try webhook first
    if await study_bot.setup_webhook():
        logger.info("🌐 Running in WEBHOOK mode")
        # Keep the thread alive
        while True:
            await asyncio.sleep(3600)
    else:
        logger.info("🔄 Running in POLLING mode")
        await study_bot.application.run_polling()

if __name__ == '__main__':
    # Start Flask
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask server started")
    
    # Run bot
    asyncio.run(main())
