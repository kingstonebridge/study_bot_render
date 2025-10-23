import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from fastapi import FastAPI, Request, Response

# === CONFIGURATION ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # e.g., https://your-app-name.onrender.com
PORT = int(os.environ.get('PORT', '10000'))

if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set!")
    exit(1)
if not WEBHOOK_URL:
    print("❌ CRITICAL: WEBHOOK_URL not set!")
    exit(1)

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== BOT LOGIC ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text("🚀 Bot is up and running! 🎉")

# ==================== FASTAPI APP FOR WEBHOOK ====================
app = FastAPI()
ptb_application = Application.builder().token(BOT_TOKEN).build()

@app.on_event("startup")
async def startup_event():
    """Set webhook on app startup"""
    logger.info(f"🔄 Setting Webhook to: {WEBHOOK_URL}/webhook")
    try:
        await ptb_application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info("✅ Webhook set successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

@app.get("/")
def home():
    """Health check endpoint"""
    return {"status": "ok", "message": "Bot is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    """Main webhook endpoint to process updates from Telegram"""
    try:
        update_json = await request.json()
        update = Update.de_json(update_json, ptb_application.bot)
        await ptb_application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return Response(content=f"Error: {e}", status_code=500)

# Set up command handlers
ptb_application.add_handler(CommandHandler("start", start))

if __name__ == '__main__':
    import uvicorn
    print(f"🚀 Starting FastAPI app locally on 0.0.0.0:{PORT}...")
    uvicorn.run(app, host='0.0.0.0', port=PORT)
