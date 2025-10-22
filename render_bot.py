
import os
import logging
import json
import time
import requests
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# FastAPI for the web server component
from fastapi import FastAPI, Request, Response

# === CONFIGURATION ===
# IMPORTANT: You must set these environment variables on Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # e.g., https://your-app-name.onrender.com
PORT = int(os.environ.get('PORT', '10000'))
LISTEN_ADDRESS = '0.0.0.0'

if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set!")
    exit(1)
if not WEBHOOK_URL:
    print("❌ CRITICAL: WEBHOOK_URL not set!")
    exit(1)

BOT_USERNAME = os.environ.get('BOT_USERNAME', '')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_ID = os.environ.get('ADMIN_ID', '')
BINANCE_WALLET = os.environ.get('BINANCE_WALLET_ADDRESS', '')

print("🚀 Starting Study Helper Pro Bot...")
print(f"🤖 Bot Username: @{BOT_USERNAME}")
print(f"👤 Admin Username: @{ADMIN_USERNAME}")
# === END CONFIGURATION ===

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== SIMPLE DATABASE (IN-MEMORY) ====================
# NOTE: This will reset on every deploy/restart. For production, use a persistent DB.
users_db = {}
payments_db = {}
earnings = {'total': 0, 'monthly': 0, 'payments': []}

# ==================== BOT LOGIC ====================
class StudyBot:
    def __init__(self, application: Application):
        self.application = application
        self.setup_handlers()
        logger.info("✅ Study Bot Handlers Initialized!")

    def setup_handlers(self):
        """Setup all bot handlers"""
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

    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test command"""
        await update.message.reply_text("✅ **Bot is WORKING!** 🎉\n\nNow try /start", parse_mode='Markdown')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        user_id = user.id

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
🔔 **Set smart study reminders**
📊 **Analyze your study patterns**
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both command and callback query for 'start'/'menu'
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')

    async def subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List subjects"""
        user_id = update.effective_user.id
        user = users_db.get(user_id, {'subjects': [], 'premium': False})
        subjects = user.get('subjects', [])
        
        if subjects:
            subject_list = "\n".join([f"• {s}" for s in subjects])
            max_subs = 15 if user.get('premium') else 3
            text = f"📚 **Your Subjects** ({len(subjects)}/{max_subs}):\n\n{subject_list}"
        else:
            text = "📚 **No subjects yet!**\n\nUse `add mathematics` to add your first subject! 🎯"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')

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
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')

    async def earnings_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin earnings"""
        user_id = str(update.effective_user.id)
        if user_id != ADMIN_ID:
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
        user_id = str(update.effective_user.id)
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return
        
        if context.args:
            memo = context.args[0]
            if memo in payments_db:
                payment = payments_db[memo]
                target_user_id = payment['user_id']
                
                if target_user_id in users_db:
                    users_db[target_user_id]['premium'] = True
                
                earnings['total'] += payment['amount']
                earnings['monthly'] += payment['amount']
                earnings['payments'].append(payment)
                
                await update.message.reply_text(f"✅ Premium activated for user {target_user_id}")
                
                try:
                    await self.application.bot.send_message(
                        chat_id=target_user_id,
                        text="🎉 **Payment Confirmed! Welcome to Premium!** 🚀",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Could not send confirmation message to user {target_user_id}: {e}")
            else:
                await update.message.reply_text("❌ Payment not found")
        else:
            await update.message.reply_text("Usage: `/confirm MEMO`", parse_mode='Markdown')
    
    async def buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buttons"""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == "premium":
            await self.premium(update, context)
        elif data == "subjects":
            await self.subjects(update, context)
        elif data == "stats":
            await self.stats(update, context)
        elif data == "help":
            await self.help(update, context)
        elif data == "menu":
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

**After payment, contact @{ADMIN_USERNAME} for manual confirmation.**
            """
            
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 Back", callback_data="premium")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        text = update.message.text.lower()
        user_id = update.effective_user.id
        response = "🤖 Unrecognized command. Try `add mathematics` or use the menu buttons."
        
        if text.startswith('add '):
            subject = text[4:].strip()
            if not subject:
                response = "❌ Please specify a subject to add. E.g., `add Physics`"
            else:
                if user_id not in users_db:
                    users_db[user_id] = {'subjects': [], 'premium': False, 'study_time': 0}
                
                user = users_db[user_id]
                max_subs = 15 if user.get('premium') else 3
                
                if len(user.get('subjects', [])) >= max_subs:
                    response = f"❌ **Limit reached!** Max {max_subs} subjects.\n\n⭐ Upgrade to Premium for up to 15 subjects!"
                else:
                    user['subjects'].append(subject.title())
                    response = f"✅ **'{subject.title()}' added!** 📚\n\nYou now have {len(user['subjects'])}/{max_subs} subjects."
        
        elif text.startswith('remove '):
            subject_to_remove = text[7:].strip().title()
            if user_id in users_db and subject_to_remove in users_db[user_id].get('subjects', []):
                users_db[user_id]['subjects'].remove(subject_to_remove)
                response = f"🗑️ **'{subject_to_remove}' removed!**"
            else:
                response = f"❌ Subject '{subject_to_remove}' not found."
        
        elif text.startswith('progress '):
            parts = text.split()
            if len(parts) >= 3:
                try:
                    hours = float(parts[-1])
                    if user_id not in users_db:
                        users_db[user_id] = {'subjects': [], 'premium': False, 'study_time': 0}
                    
                    users_db[user_id]['study_time'] = users_db[user_id].get('study_time', 0) + hours
                    response = f"📊 **+{hours} hours logged!**\n\nTotal study time: {users_db[user_id]['study_time']:.1f} hours"
                except ValueError:
                    response = "❌ Invalid format. Hours must be a number. Usage: `progress [subject] [hours]` (e.g., `progress math 2.5`)"
            else:
                response = "❌ Invalid format. Usage: `progress [subject] [hours]` (e.g., `progress math 2.5`)"
        
        await update.message.reply_text(response, parse_mode='Markdown')

# ==================== FASTAPI APP FOR WEBHOOK ====================

# Build the PTB application instance
ptb_application = Application.builder().token(BOT_TOKEN).build()
# Initialize our bot logic class
study_bot = StudyBot(ptb_application)

# Initialize the FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Set webhook on app startup"""
    logger.info(f"🔄 Setting Webhook to: {WEBHOOK_URL}/webhook")
    try:
        # The `set_webhook` method is async, so we need to `await` it.
        await ptb_application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info("✅ Webhook set successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

@app.get("/")
def home():
    """Health check endpoint"""
    return {"status": "ok", "message": "Study Helper Pro Bot is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    """Main webhook endpoint to process updates from Telegram"""
    try:
        # Get the update data from the request body
        update_json = await request.json()
        # Create a Telegram Update object
        update = Update.de_json(update_json, ptb_application.bot)
        
        # Process the update using the PTB application
        await ptb_application.process_update(update)
        
        # Return a 200 OK response to Telegram
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return Response(content=f"Error: {e}", status_code=500)

if __name__ == '__main__':
    # This part is for local testing. Render will use the Gunicorn command.
    import uvicorn
    print(f"🚀 Starting FastAPI app locally on {LISTEN_ADDRESS}:{PORT}...")
    # We run the FastAPI app using uvicorn.
    # The webhook will be set on startup.
    uvicorn.run(app, host=LISTEN_ADDRESS, port=PORT)

