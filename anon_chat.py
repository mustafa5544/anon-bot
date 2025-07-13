import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import Conflict, NetworkError, TimedOut
import asyncio

print("✅ Bot is starting...")

# Get the bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is missing!")
    exit(1)

# Global state
waiting_users = []
active_chats = {}
user_gender = {}
user_pref_gender = {}

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_gender[user_id] = "ask"
    await update.message.reply_text("Welcome to Anonymous Chat!\nWhat is your gender? (Male/Female/Other)")

# Handle plain text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if user_id in user_gender and user_gender[user_id] == "ask":
        if text in ["male", "female", "other"]:
            user_gender[user_id] = text
            user_pref_gender[user_id] = "ask"
            await update.message.reply_text("Who do you want to chat with? (Male/Female/Any)")
        else:
            await update.message.reply_text("Please choose: Male, Female or Other")
        return

    if user_id in user_pref_gender and user_pref_gender[user_id] == "ask":
        if text in ["male", "female", "any"]:
            user_pref_gender[user_id] = text
            await update.message.reply_text("Done! Use /search to find a chat partner.")
        else:
            await update.message.reply_text("Please choose: Male, Female, or Any.")
        return

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

    my_gender = user_gender.get(user_id)
    my_pref = user_pref_gender.get(user_id)

    for partner_id in waiting_users:
        partner_gender = user_gender.get(partner_id)
        partner_pref = user_pref_gender.get(partner_id)

        if (my_pref in ["any", partner_gender]) and (partner_pref in ["any", my_gender]):
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

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    if isinstance(context.error, Conflict):
        print(f"⚠️ Bot conflict detected: {context.error}")
        # Wait a bit and try to restart
        await asyncio.sleep(5)
        return
    elif isinstance(context.error, (NetworkError, TimedOut)):
        print(f"⚠️ Network error: {context.error}")
        return
    else:
        print(f"❌ Update {update} caused error {context.error}")

# Main bot application setup
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    app.add_error_handler(error_handler)

    print("🚀 Bot is polling...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# Run bot
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
