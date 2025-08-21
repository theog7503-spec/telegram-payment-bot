import asyncio
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8205388771:AAGKHiEMk3KTD-uJfF-gezfdvWK7sQ5ZfNE")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1900664668"))
UPI_QR_URL = os.environ.get("UPI_QR_URL", "https://drive.google.com/file/d/1-vFGul2Bo7UOq-J6pzSc9p0C42IOIohc/view?usp=drivesdk")
UPI_ID = os.environ.get("UPI_ID", "chodhary.pankaj2")
DOWNLOAD_LINK = os.environ.get("DOWNLOAD_LINK", "https://example.com/download")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Payment tracking
user_payments = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! 🎉\n\n"
        "Use /buy to purchase our product.\n"
        "Payment via UPI only."
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_payments and "timer_task" in user_payments[user_id]:
        user_payments[user_id]["timer_task"].cancel()
    
    user_payments[user_id] = {"status": "pending"}
    
    message = (
        "📱 **Payment Details:**\n\n"
        f"UPI ID: `{UPI_ID}`\n"
        "Amount: ₹100\n\n"
        "Scan the QR code below or use the UPI ID to make payment.\n"
        "⏱️ This payment link will expire in 5 minutes!"
    )
    
    await update.message.reply_photo(
        photo=UPI_QR_URL,
        caption=message,
        parse_mode='Markdown'
    )
    
    timer_task = asyncio.create_task(payment_timeout(user_id, context))
    user_payments[user_id]["timer_task"] = timer_task

async def payment_timeout(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        await asyncio.sleep(300)
        
        if user_id in user_payments and user_payments[user_id]["status"] == "pending":
            await context.bot.send_message(
                chat_id=user_id,
                text="⛔ Payment expired! Please try again.\n\nUse /buy to generate a new payment request."
            )
            del user_payments[user_id]
            
    except asyncio.CancelledError:
        pass

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Usage: /approve <user_id>\n"
            "Example: /approve 123456789"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    
    if target_user_id not in user_payments or user_payments[target_user_id]["status"] != "pending":
        await update.message.reply_text(f"❌ No pending payment found for user {target_user_id}")
        return
    
    if "timer_task" in user_payments[target_user_id]:
        user_payments[target_user_id]["timer_task"].cancel()
    
    user_payments[target_user_id]["status"] = "approved"
    
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"✅ Payment successful! Yeh raha tumhara download link: {DOWNLOAD_LINK}\n\n"
                 "Thank you for your purchase! 🎉"
        )
        await update.message.reply_text(f"✅ Payment approved for user {target_user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    del user_payments[target_user_id]

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not user_payments:
        await update.message.reply_text("No pending payments.")
        return
    
    status_text = "📊 **Pending Payments:**\n\n"
    for user_id, data in user_payments.items():
        if data["status"] == "pending":
            status_text += f"User ID: `{user_id}`\n"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

def main():
    print("Starting bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("status", status))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not found!")
        exit(1)
    if not ADMIN_ID:
        print("ERROR: ADMIN_ID not found!")
        exit(1)
    main()
