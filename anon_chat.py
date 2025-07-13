import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

print("✅ Bot is starting...")

# Get the bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is missing!")
    exit(1)

# Global state - simplified
waiting_users = []
active_chats = {}

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Anonymous Chat!\nUse /search to find a chat partner.")

# Handle plain text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if partner_id:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)

# Handle /search command
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_chats:
        await update.message.reply_text("You're already chatting. Use /next to skip.")
        return

    # Find a partner
    for partner_id in waiting_users:
        if partner_id != user_id:
            waiting_users.remove(partner_id)
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id

            await context.bot.send_message(chat_id=user_id, text="Connected! Say hi!")
            await context.bot.send_message(chat_id=partner_id, text="Connected! Say hi!")
            return

    waiting_users.append(user_id)
    await update.message.reply_text("Waiting for a partner...")

# Handle /next command
async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.pop(user_id, None)

    if partner_id:
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="Your partner left. Use /search to find someone new.")

    await search(update, context)

# Handle /stop command
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            await context.bot.send_message(chat_id=partner_id, text="Your partner left the chat.")

    await update.message.reply_text("You left the chat. Use /search to find someone else.")

# Main bot application setup
async def main():
    print("🔧 Setting up bot application...")
    
    # Create the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is polling...")
    # Start the Bot
    await app.run_polling(drop_pending_updates=True)

# Run bot
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
