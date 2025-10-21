import os
import logging
import json
import time
import requests 
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify

# === CONFIGURATION ===
# IMPORTANT: You must set these environment variables on Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # e.g., https://study-bot-render-1.onrender.com/webhook
PORT = int(os.environ.get('PORT', '10000')) # Render default port
LISTEN_ADDRESS = '0.0.0.0' # Listen on all interfaces

if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set!")
    exit(1)
if not WEBHOOK_URL:
    print("❌ CRITICAL: WEBHOOK_URL not set!")
    # NOTE: While you can run without it, it's best to set the full URL for clarity
    # If not set, it will be constructed dynamically, but setting it is safer.
    # For this final code, we'll ensure the webhook can be set.

BOT_USERNAME = os.environ.get('BOT_USERNAME', '')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_ID = os.environ.get('ADMIN_ID', '')
BINANCE_WALLET = os.environ.get('BINANCE_WALLET_ADDRESS', '')

print("🚀 Starting Study Helper Pro Bot...")
print(f"🤖 Bot: @{BOT_USERNAME}")
print(f"👤 Admin: @{ADMIN_USERNAME}")
# === END CONFIGURATION ===

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== SIMPLE DATABASE (IN-MEMORY) ====================
# NOTE: For production, this should be replaced with a persistent DB (e.g., PostgreSQL).
# For now, it will reset on every deploy/restart.
users_db = {}
payments_db = {}
earnings = {'total': 0, 'monthly': 0, 'payments': []}

class StudyBot:
    def __init__(self, application):
        # We pass the application instance from the main thread
        self.application = application
        self.setup_handlers()
        logger.info("✅ Study Bot Ready!")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # ... (Your existing handler setup remains the same) ...
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("test", self.test))
        self.application.add_handler(CommandHandler("premium", self.premium))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("subjects", self.subjects))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("earnings", self.earnings_cmd))
        self.application.add_handler(CommandHandler("confirm", self.confirm))
        
        self.application.add_handler(CallbackQueryHandler(self.buttons))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.messages))

    # ... (Your existing async methods for commands/messages remain the same) ...
    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test command"""
        await update.message.reply_text("✅ **Bot is WORKING!** 🎉\n\nNow try /start", parse_mode='Markdown')
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        user_id = user.id
        
        # Initialize user
        if user_id not in users_db:
            users_db[user_id] = {
                'subjects': [],
                'premium': False,
                'study_time': 0,
                'joined': datetime.now().isoformat()
            }
        
        welcome = f"""
🎓 **Welcome to Study Helper Pro, {user.first_name}!** 🤖

**Your AI study assistant:**

📚 **Organize subjects & track progress**
🔔 **Set smart study reminders** 📊 **Analyze your study patterns**
🎯 **Create optimal study plans**

🆓 **Free:** 3 subjects • 2 reminders
⭐ **Premium:** 15 subjects • 20 reminders • AI helper

**Choose an option below!** 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Manage Subjects", callback_data="subjects")],
            [InlineKeyboardButton("⭐ Get Premium", callback_data="premium")],
            [InlineKeyboardButton("📊 My Stats", callback_data="stats"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        logger.info(f"✅ Welcome sent to {user.first_name}")

    async def premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Premium info"""
        text = """
⭐ **Study Helper Pro Premium**

💎 **Plans:**
• Monthly: $5
• Quarterly: $12  
• Yearly: $40

✨ **Premium Features:**
• 15 subjects (instead of 3)
• 20 smart reminders
• AI Study Helper
• Advanced analytics

**Choose a plan below!** 👇
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 Monthly - $5", callback_data="buy_monthly")],
            [InlineKeyboardButton("📦 Quarterly - $12", callback_data="buy_quarterly")],
            [InlineKeyboardButton("🎯 Yearly - $40", callback_data="buy_yearly")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu")]
        ]
        
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        text = f"""
❓ **How to Use**

**Commands:**
• `/start` - Main menu
• `/premium` - Upgrade options
• `/subjects` - List subjects
• `/stats` - Your statistics

**Subject Management:**
• `add mathematics` - Add subject
• `remove math` - Remove subject

**Need help?** Contact @{ADMIN_USERNAME}
        """
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')

    async def subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List subjects"""
        user_id = update.effective_user.id
        user = users_db.get(user_id, {'subjects': []})
        subjects = user.get('subjects', [])
        
        if subjects:
            subject_list = "\n".join([f"• {s}" for s in subjects])
            max_subs = 15 if user.get('premium') else 3
            text = f"📚 **Your Subjects** ({len(subjects)}/{max_subs}):\n\n{subject_list}"
        else:
            text = "📚 **No subjects yet!**\n\nUse `add mathematics` to add your first subject! 🎯"
        
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show stats"""
        user_id = update.effective_user.id
        user = users_db.get(user_id, {'subjects': [], 'study_time': 0, 'premium': False})
        
        text = f"""
📊 **Your Study Stats**

👤 **Account:** {'⭐ PREMIUM' if user.get('premium') else '🆓 FREE'}
📚 **Subjects:** {len(user.get('subjects', []))}
⏱️ **Study Time:** {user.get('study_time', 0)} hours

🎯 **Keep studying!** 📚
        """
        
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')

    async def earnings_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin earnings"""
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return
        
        text = f"""
💰 **Earnings Report**

📊 **Total:** ${earnings['total']}
📈 **Monthly:** ${earnings['monthly']}
👥 **Payments:** {len(earnings['payments'])}

**Admin:** @{ADMIN_USERNAME}
        """
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm payment"""
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return
        
        if context.args:
            memo = context.args[0]
            if memo in payments_db:
                payment = payments_db[memo]
                user_id = payment['user_id']
                
                # Activate premium
                if user_id in users_db:
                    users_db[user_id]['premium'] = True
                
                # Track earnings
                earnings['total'] += payment['amount']
                earnings['monthly'] += payment['amount']
                earnings['payments'].append(payment)
                
                await update.message.reply_text(f"✅ Premium activated for user {user_id}")
                
                # Notify user
                try:
                    # NOTE: context.bot.send_message is not awaitable in some context types,
                    # but since this is an admin command, we'll try to send it.
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text="🎉 **Payment Confirmed! Welcome to Premium!** 🚀",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Could not send confirmation message to user {user_id}: {e}")
            else:
                await update.message.reply_text("❌ Payment not found")
        else:
            await update.message.reply_text("Usage: `/confirm MEMO`", parse_mode='Markdown')
    
    async def buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buttons"""
        query = update.callback_query
        # Acknowledge the query immediately
        await query.answer()
        data = query.data
        
        # NOTE: Using a button to trigger a command handler is slightly redundant
        # but following the original structure.
        if data == "premium":
            await self.premium(update, context)
        elif data == "subjects":
            await self.subjects(update, context)
        elif data == "stats":
            await self.stats(update, context)
        elif data == "help":
            # The help command originally replies to a message, which is impossible 
            # for a callback query, so we'll adapt it to edit the message.
            await self.help(update, context)
        elif data == "menu":
            # The start command replies to a message, which is impossible 
            # for a callback query, so we'll adapt it to edit the message to main menu.
            await self.start(update, context)
        elif data.startswith("buy_"):
            plan = data[4:]
            prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
            amount = prices.get(plan, 5)
            
            memo = f"STUDY{query.from_user.id}{int(time.time())}"
            payments_db[memo] = {
                'user_id': query.from_user.id,
                'amount': amount,
                'plan': plan,
                'memo': memo,
                'username': query.from_user.username or query.from_user.first_name
            }
            
            text = f"""
💎 **{plan.capitalize()} Plan - ${amount}**

📍 **Send to:** `{BINANCE_WALLET}`

📝 **Memo:** `{memo}`

🌐 **Network:** TRC20

**After payment, contact @{ADMIN_USERNAME}**
            """
            
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 Back", callback_data="premium")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages"""
        text = update.message.text.lower()
        user_id = update.effective_user.id
        
        response = "🤖 Try: `add mathematics` or use the buttons below!" # Default response
        
        if text.startswith('add '):
            # ... (Your existing 'add' logic) ...
            subject = text[4:].strip()
            if user_id not in users_db:
                users_db[user_id] = {'subjects': [], 'premium': False, 'study_time': 0}
            
            user = users_db[user_id]
            max_subs = 15 if user.get('premium') else 3
            
            if len(user.get('subjects', [])) >= max_subs:
                response = f"❌ **Limit reached!** Max {max_subs} subjects.\n\n⭐ Upgrade for 15 subjects!"
            else:
                if 'subjects' not in user:
                    user['subjects'] = []
                # Ensure case is preserved for display, use title case
                user['subjects'].append(subject.title())
                response = f"✅ **'{subject.title()}' added!** 📚\n\nYou have {len(user['subjects'])}/{max_subs} subjects."
        
        elif text.startswith('remove '):
            # ... (Your existing 'remove' logic) ...
            subject = text[7:].strip().title()
            if user_id in users_db and subject in users_db[user_id].get('subjects', []):
                users_db[user_id]['subjects'].remove(subject)
                response = f"🗑️ **'{subject}' removed!**"
            else:
                response = f"❌ Subject '{subject}' not found."
        
        elif text == 'subjects':
            # ... (Your existing 'subjects' logic) ...
            user = users_db.get(user_id, {'subjects': []})
            subjects = user.get('subjects', [])
            if subjects:
                subject_list = "\n".join([f"• {s}" for s in subjects])
                response = f"📚 **Your Subjects:**\n\n{subject_list}"
            else:
                response = "📚 **No subjects yet!**\n\nUse `add mathematics`"
        
        elif text.startswith('progress '):
            # ... (Your existing 'progress' logic) ...
            parts = text.split()
            if len(parts) >= 3:
                try:
                    hours = float(parts[2])
                    if user_id not in users_db:
                        users_db[user_id] = {'subjects': [], 'premium': False, 'study_time': 0}
                    users_db[user_id]['study_time'] = users_db[user_id].get('study_time', 0) + hours
                    response = f"📊 **+{hours} hours logged!**\n\nTotal: {users_db[user_id]['study_time']} hours"
                except ValueError: # Catch non-float for hours
                    response = "❌ Usage: `progress subject hours` (Hours must be a number e.g., 2.5)"
                except:
                    response = "❌ Use: `progress subject hours`"
            else:
                response = "❌ Use: `progress subject hours`"
        
        # Send the determined response
        await update.message.reply_text(response, parse_mode='Markdown')


# ==================== FLASK APP FOR WEBHOOK ====================

app = Flask(__name__)

# Build the bot application instance ONCE
application = Application.builder().token(BOT_TOKEN).build()
study_bot = StudyBot(application)

# Setup webhook on startup
@app.before_request
def set_webhook_if_needed():
    # Only try to set webhook once when the app starts
    if not hasattr(app, 'webhook_set') or not app.webhook_set:
        print(f"🔄 Setting Webhook to: {WEBHOOK_URL}")
        # The URL must be in the format: https://<render-url>/webhook
        # We assume the user has set the full WEBHOOK_URL environment variable
        
        # NOTE: We use context.application.bot.set_webhook() but since it's an async 
        # call that needs to be done *before* the bot starts processing updates, 
        # and we are inside a Flask context, we'll run it manually in the 
        # main thread on app start.
        
        import requests
        telegram_set_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        
        try:
            response = requests.get(telegram_set_webhook_url)
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                print(f"✅ Webhook set successfully: {result.get('description')}")
                app.webhook_set = True
            else:
                print(f"❌ Failed to set webhook: {result.get('description')}")
        except Exception as e:
            print(f"❌ Error setting webhook: {e}")

# The health check and main route remain the same
@app.route('/')
def home():
    return "✅ Study Helper Pro Bot is running! (Awaiting Webhook updates)", 200

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# This is the crucial Webhook endpoint
@app.route('/webhook', methods=['POST'])
async def webhook():
    # Check if the request is from Telegram
    if request.headers.get('Content-Type') == 'application/json':
        try:
            # Get the update data from the request body
            update_json = request.get_json(force=True)
            # Create a Telegram Update object
            update = Update.de_json(update_json, study_bot.application.bot)
            
            # Process the update using the application's internal update processor
            # NOTE: We run this asynchronously using `application.process_update()`
            # which is the correct way to process webhook updates in ptb v20+.
            await study_bot.application.process_update(update)
            
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        # Ignore non-json requests
        return 'Method Not Allowed', 405

if __name__ == '__main__':
    # Use gunicorn on Render by convention, but for local testing or simple
    # setup, we use Flask's built-in server with the specified port and address.
    # On Render, the build process will likely use gunicorn `gunicorn render_bot:app`
    # and set the port via environment variable.
    print(f"🚀 Starting Flask app on {LISTEN_ADDRESS}:{PORT}...")
    
    # We run the Flask app. The /webhook endpoint will now handle all bot traffic.
    app.run(host=LISTEN_ADDRESS, port=PORT, debug=False)

