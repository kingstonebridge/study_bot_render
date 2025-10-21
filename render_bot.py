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
    logging.error("❌ BOT_TOKEN not set!")
    exit(1)

BOT_USERNAME = os.environ.get('BOT_USERNAME', 'StudyHelperProBot')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_ID = os.environ.get('ADMIN_ID', '')  # Your Telegram ID
BINANCE_WALLET = os.environ.get('BINANCE_WALLET_ADDRESS', '')
# === END CONFIGURATION ===

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

# ==================== PAYMENT & EARNINGS SYSTEM ====================
class PaymentSystem:
    def __init__(self):
        self.wallet_address = BINANCE_WALLET
        self.pending_payments = {}
        self.earnings_data = {
            'total_earned': 0,
            'monthly_earned': 0,
            'total_users': 0,
            'all_time_payments': []
        }
        self.load_earnings()
    
    def create_payment(self, user_id, amount, plan_type, username):
        """Create payment with unique memo"""
        try:
            memo = f"STUDY{plan_type.upper()}{user_id}{int(time.time())}"
            
            payment_data = {
                'wallet_address': self.wallet_address,
                'amount': amount,
                'currency': 'USDT',
                'network': 'TRC20',
                'memo': memo,
                'user_id': user_id,
                'username': username,
                'plan_type': plan_type,
                'created_at': time.time(),
                'status': 'pending'
            }
            
            self.pending_payments[memo] = payment_data
            logger.info(f"💰 Payment created: {memo} - ${amount} - @{username}")
            return payment_data
            
        except Exception as e:
            logger.error(f"❌ Payment creation error: {e}")
            return None
    
    def confirm_payment(self, memo):
        """Manually confirm payment and track earnings"""
        if memo not in self.pending_payments:
            return False
        
        payment = self.pending_payments[memo]
        payment['status'] = 'confirmed'
        payment['confirmed_at'] = time.time()
        
        # Track earnings
        self.earnings_data['total_earned'] += payment['amount']
        self.earnings_data['monthly_earned'] += payment['amount']
        self.earnings_data['total_users'] += 1
        
        # Add to payment history
        self.earnings_data['all_time_payments'].append({
            'memo': memo,
            'amount': payment['amount'],
            'plan_type': payment['plan_type'],
            'user_id': payment['user_id'],
            'username': payment['username'],
            'timestamp': time.time()
        })
        
        self.save_earnings()
        logger.info(f"✅ Payment confirmed: {memo} - ${payment['amount']}")
        return True
    
    def get_payment(self, memo):
        return self.pending_payments.get(memo)
    
    def get_earnings_stats(self):
        return self.earnings_data
    
    def get_user_payments(self, user_id):
        return [p for p in self.pending_payments.values() if p['user_id'] == user_id]
    
    def save_earnings(self):
        try:
            with open('earnings.json', 'w') as f:
                json.dump(self.earnings_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Earnings save error: {e}")
    
    def load_earnings(self):
        try:
            with open('earnings.json', 'r') as f:
                self.earnings_data = json.load(f)
        except FileNotFoundError:
            self.save_earnings()

# ==================== DATABASE SYSTEM ====================
class Database:
    def __init__(self):
        self.file_path = 'users.json'
    
    def get_user(self, user_id):
        try:
            with open(self.file_path, 'r') as f:
                users = json.load(f)
                return users.get(str(user_id), self.default_user(user_id))
        except FileNotFoundError:
            return self.default_user(user_id)
    
    def save_user(self, user_id, user_data):
        try:
            # Read existing
            try:
                with open(self.file_path, 'r') as f:
                    users = json.load(f)
            except FileNotFoundError:
                users = {}
            
            # Update user
            users[str(user_id)] = user_data
            
            # Save back
            with open(self.file_path, 'w') as f:
                json.dump(users, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
    
    def default_user(self, user_id):
        return {
            'user_id': user_id,
            'subjects': [],
            'reminders': [],
            'is_premium': False,
            'premium_until': None,
            'study_time': 0,
            'sessions': 0,
            'joined_date': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }

# Initialize systems
payment_system = PaymentSystem()
database = Database()

# ==================== TELEGRAM BOT ====================
class StudyBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        logger.info("✅ Study Helper Pro Bot initialized!")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("premium", self.premium_info))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subjects", self.list_subjects))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("earnings", self.earnings_stats))  # Admin
        self.application.add_handler(CommandHandler("confirm", self.confirm_payment))  # Admin
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    # ==================== USER COMMANDS ====================
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        # Save/update user
        user_data = database.get_user(user_id)
        user_data['last_active'] = datetime.now().isoformat()
        database.save_user(user_id, user_data)
        
        welcome_text = f"""
🎓 **Welcome to Study Helper Pro, {user.first_name}!** 🤖

**Your AI-powered study assistant:**

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

🆓 **Free Plan:** 3 subjects • 2 reminders • Basic analytics
⭐ **Premium Features:** 15 subjects • 20 reminders • AI helper • Advanced analytics

**Choose an option below to get started!** 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Manage Subjects", callback_data="subjects")],
            [InlineKeyboardButton("🔔 Set Reminder", callback_data="set_reminder")],
            [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="premium"),
             InlineKeyboardButton("📊 My Stats", callback_data="stats")],
            [InlineKeyboardButton("🎯 Study Tools", callback_data="tools"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    
    async def premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        premium_text = f"""
⭐ **Study Helper Pro Premium**

🚀 **Supercharge your learning experience!**

✨ **Premium Benefits:**
• 📚 15 subjects (instead of 3)
• 🔔 20 smart reminders (instead of 2)  
• 🤖 AI Study Helper & personalized tips
• 📊 Advanced progress analytics
• 📱 Export schedules to calendar
• 🎯 Smart study plan generator
• ⚡ Priority support

💎 **Pricing:**
• **Monthly:** $5 USD
• **Quarterly:** $12 USD (20% off)  
• **Yearly:** $40 USD (33% off)

🔒 **30-day money-back guarantee**

**Ready to upgrade? Choose a plan below!** 👇
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 Monthly - $5", callback_data="buy_monthly")],
            [InlineKeyboardButton("📦 Quarterly - $12", callback_data="buy_quarterly")],
            [InlineKeyboardButton("🎯 Yearly - $40", callback_data="buy_yearly")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        if update.message:
            await update.message.reply_text(premium_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(premium_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""
❓ **How to Use Study Helper Pro**

🎯 **Quick Commands:**
• `/start` - Main menu
• `/premium` - Upgrade options  
• `/subjects` - List your subjects
• `/stats` - Your study statistics

📚 **Subject Management:**
• `add mathematics` - Add subject
• `remove math` - Remove subject
• `subjects` - List subjects

🔔 **Study Tools:**
• `remind study math 18:00` - Set reminder
• `progress math 2` - Log 2 hours studied
• `timer 25` - Start study timer

💎 **Premium Upgrade:**
1. Choose plan below
2. Send USDT to Binance address
3. Include unique MEMO
4. Contact @{ADMIN_USERNAME} if needed

**Need help? Contact @{ADMIN_USERNAME}**
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="premium")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def list_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = database.get_user(user_id)
        subjects = user_data.get('subjects', [])
        
        if not subjects:
            response = "📚 **Your Subjects:**\n\nNo subjects added yet!\n\nUse **'add mathematics'** to add your first subject! 🎯"
        else:
            subject_list = "\n".join([f"• {subject}" for subject in subjects])
            max_subjects = 15 if user_data.get('is_premium') else 3
            response = f"📚 **Your Subjects:** ({len(subjects)}/{max_subjects})\n\n{subject_list}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = database.get_user(user_id)
        
        stats_text = f"""
📊 **Your Study Statistics**

👤 **Account:** {'⭐ PREMIUM' if user_data.get('is_premium') else '🆓 FREE'}
📚 **Subjects:** {len(user_data.get('subjects', []))}/{15 if user_data.get('is_premium') else 3}
⏱️ **Study Time:** {user_data.get('study_time', 0)} hours
📅 **Sessions:** {user_data.get('sessions', 0)}
🔔 **Reminders:** {len(user_data.get('reminders', []))}/{20 if user_data.get('is_premium') else 2}

🎯 **Keep up the great work!**
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="premium")] if not user_data.get('is_premium') else [],
            [InlineKeyboardButton("📚 Manage Subjects", callback_data="subjects")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        if update.message:
            await update.message.reply_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # ==================== PAYMENT HANDLING ====================
    async def handle_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type):
        query = update.callback_query
        user = query.from_user
        user_id = user.id
        
        prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
        amount = prices.get(plan_type, 5)
        
        # Create payment
        payment_data = payment_system.create_payment(
            user_id, amount, plan_type, user.username or user.first_name
        )
        
        if not payment_data:
            await query.edit_message_text(
                "❌ Payment system error. Please contact admin.",
                parse_mode='Markdown'
            )
            return
        
        payment_text = f"""
💎 **Premium Upgrade - {plan_type.capitalize()} Plan**

💰 **Amount:** ${amount} USDT
📍 **Wallet Address:** 
`{payment_data['wallet_address']}`

📝 **MEMO (IMPORTANT):**
`{payment_data['memo']}`

🌐 **Network:** TRC20 (TRON)
⏰ **Valid for:** 24 hours

📋 **Payment Instructions:**

1. **Send {amount} USDT** via TRC20 network
2. **Include the MEMO** exactly as shown
3. **Contact @{ADMIN_USERNAME}** after payment
4. **Premium activated** within 1 hour

💡 **Need help?** Contact @{ADMIN_USERNAME}
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton("📋 Payment Help", callback_data="payment_help")],
            [InlineKeyboardButton("🔙 Back to Plans", callback_data="premium")]
        ]
        
        await query.edit_message_text(
            payment_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== ADMIN COMMANDS ====================
    async def earnings_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin: Check earnings statistics"""
        user_id = update.effective_user.id
        
        # Check if admin
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        earnings = payment_system.get_earnings_stats()
        
        earnings_text = f"""
💰 **EARNINGS REPORT** 💰

📊 **Total Earnings:** ${earnings['total_earned']} USDT
📈 **This Month:** ${earnings['monthly_earned']} USDT  
👥 **Premium Users:** {earnings['total_users']}

💎 **Recent Payments:**
"""
        
        # Show last 10 payments
        recent = earnings['all_time_payments'][-10:]
        for payment in reversed(recent):
            date = datetime.fromtimestamp(payment['timestamp']).strftime('%m/%d %H:%M')
            earnings_text += f"• ${payment['amount']} - {payment['plan_type']} - @{payment['username']} - {date}\n"
        
        earnings_text += f"\n📱 **Admin:** @{ADMIN_USERNAME}"
        
        await update.message.reply_text(earnings_text, parse_mode='Markdown')
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin: Manually confirm a payment"""
        user_id = update.effective_user.id
        
        # Check if admin
        if str(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /confirm MEMO")
            return
        
        memo = context.args[0]
        
        if payment_system.confirm_payment(memo):
            payment_data = payment_system.get_payment(memo)
            user_id = payment_data['user_id']
            
            # Activate premium
            user_data = database.get_user(user_id)
            user_data['is_premium'] = True
            
            # Set duration
            duration = {"monthly": 30, "quarterly": 90, "yearly": 365}
            premium_days = duration.get(payment_data['plan_type'], 30)
            user_data['premium_until'] = (datetime.now() + timedelta(days=premium_days)).isoformat()
            
            database.save_user(user_id, user_data)
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 **Payment Confirmed! Welcome to Premium!** 💎\n\nYour {payment_data['plan_type']} plan is now active for {premium_days} days! 🚀",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"❌ Could not notify user: {e}")
            
            await update.message.reply_text(
                f"✅ Premium activated for user {user_id} (@{payment_data['username']}) - ${payment_data['amount']} {payment_data['plan_type']}"
            )
        else:
            await update.message.reply_text("❌ Payment not found or already confirmed")
    
    # ==================== BUTTON HANDLER ====================
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "premium":
            await self.premium_info(update, context)
        
        elif data.startswith("buy_"):
            plan = data[4:]
            await self.handle_payment(update, context, plan)
        
        elif data == "subjects":
            user_data = database.get_user(user_id)
            subjects = user_data.get('subjects', [])
            max_subjects = 15 if user_data.get('is_premium') else 3
            
            if not subjects:
                text = f"📚 **No subjects yet!**\n\nUse 'add mathematics' to add subjects.\n\n**Limit:** {max_subjects} subjects"
            else:
                subject_list = "\n".join([f"• {s}" for s in subjects])
                text = f"📚 **Your Subjects** ({len(subjects)}/{max_subjects}):\n\n{subject_list}"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif data == "stats":
            await self.show_stats(update, context)
        
        elif data == "payment_help":
            help_text = f"""
💳 **Payment Help**

1. **Send USDT via TRC20** to the address provided
2. **INCLUDE THE MEMO** - this is crucial!
3. **Contact @{ADMIN_USERNAME}** if you need help
4. **Wait for confirmation** (usually within 1 hour)

**Need immediate help?** Contact @{ADMIN_USERNAME}
            """
            await query.edit_message_text(help_text, parse_mode='Markdown')
        
        elif data == "main_menu":
            await self.start(update, context)
        
        elif data == "help":
            await self.help_command(update, context)
    
    # ==================== MESSAGE HANDLER ====================
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text.lower()
        user_id = update.effective_user.id
        user_data = database.get_user(user_id)
        
        # Update last active
        user_data['last_active'] = datetime.now().isoformat()
        
        if user_message.startswith('add '):
            subject = user_message[4:].strip()
            if subject:
                max_subjects = 15 if user_data.get('is_premium') else 3
                current = len(user_data.get('subjects', []))
                
                if current >= max_subjects:
                    response = f"❌ **Limit reached!** You can only have {max_subjects} subjects.\n\n⭐ **Upgrade to premium** for 15 subjects!"
                else:
                    if 'subjects' not in user_data:
                        user_data['subjects'] = []
                    user_data['subjects'].append(subject.title())
                    database.save_user(user_id, user_data)
                    response = f"✅ **'{subject.title()}' added!** 📚\n\nYou now have {len(user_data['subjects'])}/{max_subjects} subjects."
        
        elif user_message.startswith('remove '):
            subject = user_message[7:].strip().title()
            subjects = user_data.get('subjects', [])
            if subject in subjects:
                subjects.remove(subject)
                user_data['subjects'] = subjects
                database.save_user(user_id, user_data)
                response = f"🗑️ **'{subject}' removed!**"
            else:
                response = f"❌ Subject '{subject}' not found."
        
        elif user_message == 'subjects':
            subjects = user_data.get('subjects', [])
            if not subjects:
                response = "📚 **No subjects yet!**\n\nUse 'add mathematics' to add your first subject!"
            else:
                subject_list = "\n".join([f"• {s}" for s in subjects])
                max_subjects = 15 if user_data.get('is_premium') else 3
                response = f"📚 **Your Subjects** ({len(subjects)}/{max_subjects}):\n\n{subject_list}"
        
        elif user_message.startswith('progress '):
            parts = user_message.split()
            if len(parts) >= 3:
                try:
                    hours = float(parts[2])
                    user_data['study_time'] = user_data.get('study_time', 0) + hours
                    user_data['sessions'] = user_data.get('sessions', 0) + 1
                    database.save_user(user_id, user_data)
                    response = f"📊 **Progress logged!** +{hours} hours\n\n**Total:** {user_data['study_time']} hours"
                except:
                    response = "❌ Use: `progress math 2.5`"
            else:
                response = "❌ Use: `progress subject hours`"
        
        else:
            responses = [
                "I'm here to help with your studies! 📚 Use the menu or type 'help' for guidance.",
                "Need study assistance? Try adding subjects or check out premium features! 🎯",
                "Use the buttons below to navigate, or type 'help' for commands! 🤖"
            ]
            import random
            response = random.choice(responses)
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def setup_webhook(self):
        """Setup webhook for production"""
        try:
            if os.environ.get('RENDER'):
                webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
                await self.application.bot.set_webhook(webhook_url)
                logger.info(f"✅ Webhook configured: {webhook_url}")
                return True
        except Exception as e:
            logger.error(f"❌ Webhook setup failed: {e}")
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
        <title>Study Helper Pro - AI Study Assistant</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px; border-radius: 15px; text-align: center; }
            .btn { background: #25D366; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; margin: 10px; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Study Helper Pro</h1>
            <p>Your AI-powered study assistant on Telegram</p>
            <a href="https://t.me/StudyHelperProBot" class="btn">🚀 Start Studying Smarter</a>
        </div>
        <div style="text-align: center; margin-top: 40px;">
            <h2>💰 Real Payments • 📊 Progress Tracking • 🎯 Smart Reminders</h2>
        </div>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(), study_bot.application.bot)
        asyncio.run(study_bot.application.process_update(update))
        return 'ok'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'error', 500

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'Study Helper Pro'}, 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False, use_reloader=False)

async def main():
    if await study_bot.setup_webhook():
        logger.info("🌐 Bot running with webhook")
    else:
        logger.info("🔄 Bot running with polling")
        await study_bot.application.run_polling()

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(main())
