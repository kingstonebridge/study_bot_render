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
ADMIN_USERNAME = "@Kingstonebridge"  # Your Telegram @username← Your personal Telegram username without @
# === END CONFIGURATION ===

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
WEBHOOK_PORT = int(os.environ.get('PORT', 10000))

# Initialize Flask
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory storage (replace with database in production)
user_data = {}

class StudyBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("premium", self.premium_info))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subjects", self.list_subjects))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when user starts the bot"""
        user = update.effective_user
        user_id = user.id
        
        # Initialize user data if not exists
        if user_id not in user_data:
            user_data[user_id] = {
                'subjects': [],
                'reminders': [],
                'is_premium': False,
                'study_time': 0
            }
        
        welcome_text = f"""
🎓 **Welcome to Study Helper Pro, {user.first_name}!**

🤖 **Your AI-powered study assistant**

📚 **What I can do for you:**
• Organize your subjects and topics
• Set study reminders and schedules  
• Track your study progress
• Help you study more effectively

🆓 **Free Features:**
• 3 subjects • 2 reminders • Basic analytics

⭐ **Premium Features:**
• 15 subjects • 20 reminders • AI study helper
• Advanced analytics • Export features

**Click the buttons below to get started!** 🚀
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
        
        # Send welcome message with photo (optional)
        try:
            await update.message.reply_photo(
                photo="https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400",
                caption=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except:
            # Fallback to text only if photo fails
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium information"""
        premium_text = """
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

**Click below to upgrade!** 🚀
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
        help_text = f"""
❓ **How to Use Study Helper Pro**

🎯 **Quick Start:**
1. Use buttons below for easy navigation
2. Or type commands like shown below

📚 **Subject Commands:**
• `add mathematics` - Add a subject
• `remove mathematics` - Remove subject  
• `subjects` - List your subjects

🔔 **Reminder Commands:**
• `remind study math 18:00` - Set reminder
• `reminders` - View all reminders

⏰ **Study Commands:**
• `timer 25` - Start 25min study timer
• `progress math 2` - Log 2 hours studied

📊 **Other Commands:**
• `stats` - View your statistics
• `goals` - Set study goals

💡 **Pro Tip:** Buttons are easier! Use them!

**Need help? Contact @{ADMIN_USERNAME}**
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Add Subject Demo", callback_data="demo_add")],
            [InlineKeyboardButton("🔔 Reminder Demo", callback_data="demo_remind")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def list_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's subjects"""
        user_id = update.effective_user.id
        subjects = user_data.get(user_id, {}).get('subjects', [])
        
        if not subjects:
            response = "📚 **Your Subjects:**\n\nNo subjects added yet!\n\nUse 'add mathematics' to add your first subject! 🎯"
        else:
            subject_list = "\n".join([f"• {subject}" for subject in subjects])
            response = f"📚 **Your Subjects:**\n\n{subject_list}\n\nUse 'add [subject]' to add more!"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button clicks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        logger.info(f"Button pressed by {user_id}: {data}")
        
        if data == "premium":
            await self.premium_info(update, context)
        
        elif data == "subjects":
            subjects = user_data.get(user_id, {}).get('subjects', [])
            max_subjects = 15 if user_data.get(user_id, {}).get('is_premium', False) else 3
            
            if not subjects:
                subjects_text = f"""
📚 **Subject Management**

🆓 **Your Plan:** {'⭐ PREMIUM' if user_data.get(user_id, {}).get('is_premium') else 'FREE'}
📊 **Usage:** 0/{max_subjects} subjects

💡 **To add a subject, type:**
`add mathematics`

Or try the demo button below! 👇
                """
            else:
                subject_list = "\n".join([f"• {subject}" for subject in subjects])
                subjects_text = f"""
📚 **Subject Management**

🆓 **Your Plan:** {'⭐ PREMIUM' if user_data.get(user_id, {}).get('is_premium') else 'FREE'}  
📊 **Usage:** {len(subjects)}/{max_subjects} subjects

**Your Subjects:**
{subject_list}

💡 **Type 'add [subject]' to add more!**
                """
            
            keyboard = [
                [InlineKeyboardButton("🎯 Try: Add Mathematics", callback_data="demo_add")],
                [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(subjects_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "stats":
            user_info = user_data.get(user_id, {})
            subjects_count = len(user_info.get('subjects', []))
            reminders_count = len(user_info.get('reminders', []))
            study_time = user_info.get('study_time', 0)
            is_premium = user_info.get('is_premium', False)
            
            stats_text = f"""
📊 **Your Study Statistics**

👤 **Account Type:** {'⭐ PREMIUM USER' if is_premium else '🆓 FREE USER'}
📚 **Subjects:** {subjects_count}/{'15' if is_premium else '3'}
🔔 **Reminders:** {reminders_count}/{'20' if is_premium else '2'}
⏱️ **Total Study Time:** {study_time} hours
📅 **Study Sessions:** {user_info.get('sessions', 0)}

🎯 **Keep up the great work!**
{'🚀 **Premium features active!**' if is_premium else '⭐ **Upgrade to premium for advanced analytics!**'}
            """
            
            keyboard = [
                [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="premium")] if not is_premium else [],
                [InlineKeyboardButton("📚 Manage Subjects", callback_data="subjects")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "demo_add":
            user_id = query.from_user.id
            if user_id not in user_data:
                user_data[user_id] = {'subjects': [], 'reminders': [], 'is_premium': False, 'study_time': 0}
            
            # Add demo subject
            if "Mathematics" not in user_data[user_id]['subjects']:
                user_data[user_id]['subjects'].append("Mathematics")
            
            response = "✅ **Demo subject 'Mathematics' added!** 📚\n\nYou can now see it in your subjects list. Try adding more with 'add [subject]' command!"
            
            keyboard = [
                [InlineKeyboardButton("📚 View Subjects", callback_data="subjects")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data.startswith("buy_"):
            plan = data[4:]  # monthly, quarterly, yearly
            prices = {"monthly": 5, "quarterly": 12, "yearly": 40}
            periods = {"monthly": "1 month", "quarterly": "3 months", "yearly": "1 year"}
            
            payment_text = f"""
💎 **Premium Upgrade - {plan.capitalize()} Plan**

**Plan:** {plan.capitalize()} Subscription  
**Price:** ${prices[plan]} USD
**Duration:** {periods[plan]}
**Features:** 15 subjects, 20 reminders, AI helper, analytics, export

📝 **How to Upgrade:**

1. **Contact @{ADMIN_USERNAME}**
2. **Message:** "I want {plan} premium plan"
3. **You'll receive** payment instructions
4. **Activation within 1 hour** after payment

✅ **Start studying smarter with premium features!**

🔒 **30-day money-back guarantee**
            """
            
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin Now", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 View Other Plans", callback_data="premium")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        elif data == "main_menu":
            await self.start(update, context)
        
        elif data == "help":
            await self.help_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        user_message = update.message.text.lower().strip()
        user_id = update.effective_user.id
        
        logger.info(f"Message from {user_id}: {user_message}")
        
        # Initialize user data if not exists
        if user_id not in user_data:
            user_data[user_id] = {
                'subjects': [],
                'reminders': [], 
                'is_premium': False,
                'study_time': 0,
                'sessions': 0
            }
        
        # Handle subject addition
        if user_message.startswith(('add ', 'create ')):
            subject_name = user_message[4:].strip()
            if subject_name:
                max_subjects = 15 if user_data[user_id]['is_premium'] else 3
                
                if len(user_data[user_id]['subjects']) >= max_subjects:
                    response = f"❌ **Subject limit reached!**\n\nYou can only have {max_subjects} subjects on your current plan.\n\n⭐ **Upgrade to premium** for 15 subjects!"
                else:
                    user_data[user_id]['subjects'].append(subject_name.title())
                    response = f"✅ **Subject '{subject_name.title()}' added successfully!** 📚\n\nYou now have {len(user_data[user_id]['subjects'])}/{max_subjects} subjects."
            else:
                response = "❌ Please specify a subject name.\n\n**Example:** `add mathematics` or `add computer science`"
        
        # Handle subject removal
        elif user_message.startswith(('remove ', 'delete ')):
            subject_name = user_message[7:].strip().title()
            if subject_name in user_data[user_id]['subjects']:
                user_data[user_id]['subjects'].remove(subject_name)
                response = f"🗑️ **Subject '{subject_name}' removed successfully!**"
            else:
                response = f"❌ Subject '{subject_name}' not found in your list."
        
        # Handle subjects list
        elif user_message in ['subjects', 'list', 'list subjects']:
            subjects = user_data[user_id]['subjects']
            if not subjects:
                response = "📚 **Your Subjects:**\n\nNo subjects added yet!\n\nUse **'add mathematics'** to add your first subject! 🎯"
            else:
                subject_list = "\n".join([f"• {subject}" for subject in subjects])
                response = f"📚 **Your Subjects:**\n\n{subject_list}\n\nUse **'add [subject]'** to add more, or **'remove [subject]'** to delete."
        
        # Handle study time tracking
        elif user_message.startswith('progress '):
            parts = user_message.split()
            if len(parts) >= 3:
                subject = parts[1].title()
                try:
                    hours = float(parts[2])
                    user_data[user_id]['study_time'] += hours
                    user_data[user_id]['sessions'] += 1
                    response = f"📊 **Progress recorded!**\n\nAdded {hours} hours for {subject}.\n\n**Total study time:** {user_data[user_id]['study_time']} hours"
                except:
                    response = "❌ Please specify valid hours.\n\n**Example:** `progress mathematics 2.5`"
            else:
                response = "❌ Please specify subject and hours.\n\n**Example:** `progress mathematics 2.5`"
        
        # Handle stats command
        elif user_message in ['stats', 'statistics', 'my stats']:
            info = user_data[user_id]
            response = f"""
📊 **Your Study Stats:**

📚 **Subjects:** {len(info['subjects'])}/{15 if info['is_premium'] else 3}
⏱️ **Study Time:** {info['study_time']} hours
📅 **Study Sessions:** {info['sessions']}
🔔 **Reminders:** {len(info['reminders'])}/{20 if info['is_premium'] else 2}

🎯 **Keep going!** {'⭐ Premium features active!' if info['is_premium'] else 'Upgrade to premium for more!'}
            """
        
        # Default response for other messages
        else:
            responses = [
                "I'm here to help with your studies! Use the menu buttons or type **'help'** for guidance. 📚",
                "Need study assistance? Try **adding subjects** or check out our **premium features**! 🎯", 
                "Use the buttons below to navigate, or type **'help'** to see all commands! 🤖",
                "Ready to boost your productivity? Let me help organize your studies! 🚀",
                "Try **'add mathematics'** to add your first subject, or use the menu buttons! 📚"
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

# Initialize bot instance
study_bot = StudyBot()

# === UPDATED HTML WITH YOUR ACTUAL BOT ===
@app.route('/')
def home():
    your_bot_link = f"https://t.me/{BOT_USERNAME}"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Helper Pro Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-top: 20px;
            }}
            .header {{ 
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .btn {{ 
                display: inline-block; 
                background: #25D366; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 50px;
                margin: 10px;
                font-size: 18px;
                font-weight: bold;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4);
                background: #1da851;
            }}
            .features {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin: 30px 0; 
            }}
            .feature {{ 
                background: #f8f9fa; 
                padding: 25px; 
                border-radius: 10px; 
                border-left: 4px solid #667eea;
                transition: transform 0.3s ease;
            }}
            .feature:hover {{
                transform: translateY(-5px);
            }}
            .feature h3 {{
                color: #667eea;
                margin-top: 0;
            }}
            .stats {{ 
                background: #e3f2fd; 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 Study Helper Pro</h1>
                <p>Your AI-powered study assistant on Telegram</p>
                <a href="{your_bot_link}" class="btn">🚀 Start Studying Smarter</a>
                <p><small>Direct link to start chatting with your study assistant</small></p>
            </div>
            
            <div class="stats">
                <h2>📈 Transform Your Study Habits</h2>
                <p>Join students who study 40% more effectively with our AI assistant</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>📚 Smart Organization</h3>
                    <p>Organize all your subjects, track progress, and manage study schedules in one place</p>
                </div>
                <div class="feature">
                    <h3>🔔 Intelligent Reminders</h3>
                    <p>Never miss a study session with smart scheduling and timely notifications</p>
                </div>
                <div class="feature">
                    <h3>📊 Progress Analytics</h3>
                    <p>Track your study time, monitor improvement, and get personalized insights</p>
                </div>
                <div class="feature">
                    <h3>🎯 Study Planner</h3>
                    <p>Create optimized study schedules and set achievable learning goals</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <h2>Ready to Boost Your Grades?</h2>
                <p>Start your journey to academic success today</p>
                <a href="{your_bot_link}" class="btn">🎯 Launch Study Helper Pro</a>
            </div>
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
        logger.info(f"✅ Bot is LIVE at: https://t.me/{BOT_USERNAME}")
    else:
        logger.info("🔧 Bot running in POLLING mode")
        await study_bot.application.run_polling()

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(main())
