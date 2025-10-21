import os
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask
# === CONFIGURATION ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set!")
    exit(1)

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

# ==================== SIMPLE DATABASE ====================
users_db = {}
payments_db = {}
earnings = {'total': 0, 'monthly': 0, 'payments': []}

class StudyBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        logger.info("✅ Study Bot Ready!")
    
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
        await update.message.reply_text("✅ **Bot is WORKING!** 🎉\n\nNow try /start")
    
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
        await update.message.reply_text(text, parse_mode='Markdown')
    
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
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 **Payment Confirmed! Welcome to Premium!** 🚀"
                    )
                except:
                    pass
            else:
                await update.message.reply_text("❌ Payment not found")
        else:
            await update.message.reply_text("Usage: /confirm MEMO")
    
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

📍 **Send to:** 
`{BINANCE_WALLET}`

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
        
        if text.startswith('add '):
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
                user['subjects'].append(subject.title())
                response = f"✅ **'{subject.title()}' added!** 📚\n\nYou have {len(user['subjects'])}/{max_subs} subjects."
        
        elif text.startswith('remove '):
            subject = text[7:].strip().title()
            if user_id in users_db and subject in users_db[user_id].get('subjects', []):
                users_db[user_id]['subjects'].remove(subject)
                response = f"🗑️ **'{subject}' removed!**"
            else:
                response = f"❌ Subject '{subject}' not found."
        
        elif text == 'subjects':
            user = users_db.get(user_id, {'subjects': []})
            subjects = user.get('subjects', [])
            if subjects:
                subject_list = "\n".join([f"• {s}" for s in subjects])
                response = f"📚 **Your Subjects:**\n\n{subject_list}"
            else:
                response = "📚 **No subjects yet!**\n\nUse `add mathematics`"
        
        elif text.startswith('progress '):
            parts = text.split()
            if len(parts) >= 3:
                try:
                    hours = float(parts[2])
                    if user_id not in users_db:
                        users_db[user_id] = {'subjects': [], 'premium': False, 'study_time': 0}
                    users_db[user_id]['study_time'] = users_db[user_id].get('study_time', 0) + hours
                    response = f"📊 **+{hours} hours logged!**\n\nTotal: {users_db[user_id]['study_time']} hours"
                except:
                    response = "❌ Use: `progress math 2.5`"
            else:
                response = "❌ Use: `progress subject hours`"
        
        else:
            response = "🤖 Try: `add mathematics` or use the buttons below!"
        
        await update.message.reply_text(response, parse_mode='Markdown')

# Create and run bot
def main():
    print("🚀 Starting bot in POLLING mode...")
    bot = StudyBot()
    
    # Run in polling mode (this will work!)
    bot.application.run_polling()
    print("✅ Bot is now running and listening for messages!")

# ==================== FLASK APP FOR RENDER ====================
# ==================== FLASK APP FOR RENDER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Study Helper Pro Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    return 'ok'

# ==================== RUN BOT IN BACKGROUND ====================
# ==================== RUN BOT IN BACKGROUND ====================
def run_bot():
    """Run the bot in a separate thread with proper event loop"""
    print("🚀 Starting bot in POLLING mode...")
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot = StudyBot()
        loop.run_until_complete(bot.application.run_polling())
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        loop.close()

# Start bot in background thread
import threading
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print("✅ Bot started in background thread!")

if __name__ == '__main__':
    # This keeps Flask running
    app.run(host='0.0.0.0', port=10000, debug=False)
