import os
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    Filters,
)

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
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_gender[user_id] = "ask"
    update.message.reply_text("Welcome to Anonymous Chat!\nWhat is your gender? (Male/Female/Other)")

# Handle plain text messages
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if user_id in user_gender and user_gender[user_id] == "ask":
        if text in ["male", "female", "other"]:
            user_gender[user_id] = text
            user_pref_gender[user_id] = "ask"
            update.message.reply_text("Who do you want to chat with? (Male/Female/Any)")
        else:
            update.message.reply_text("Please choose: Male, Female or Other")
        return

    if user_id in user_pref_gender and user_pref_gender[user_id] == "ask":
        if text in ["male", "female", "any"]:
            user_pref_gender[user_id] = text
            update.message.reply_text("Done! Use /search to find a chat partner.")
        else:
            update.message.reply_text("Please choose: Male, Female, or Any.")
        return

    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if partner_id:
            context.bot.send_message(chat_id=partner_id, text=update.message.text)

# Handle /search command
def search(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in active_chats:
        update.message.reply_text("You're already chatting. Use /next to skip.")
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

            context.bot.send_message(chat_id=user_id, text="Connected! Say hi!")
            context.bot.send_message(chat_id=partner_id, text="Connected! Say hi!")
            return

    waiting_users.append(user_id)
    update.message.reply_text("Waiting for a partner...")

# Handle /next command
def next_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    partner_id = active_chats.pop(user_id, None)

    if partner_id:
        active_chats.pop(partner_id, None)
        context.bot.send_message(chat_id=partner_id, text="Your partner left. Use /search to find someone new.")

    search(update, context)

# Handle /stop command
def stop_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            context.bot.send_message(chat_id=partner_id, text="Your partner left the chat.")

    update.message.reply_text("You left the chat. Use /search to find someone else.")

# Error handler
def error_handler(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    print(f'Update {update} caused error {context.error}')

# Main bot application setup
def main():
    print("🔧 Setting up bot application...")
    
    # Create the Updater and pass it your bot's token
    updater = Updater(token=BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("search", search))
    dispatcher.add_handler(CommandHandler("next", next_chat))
    dispatcher.add_handler(CommandHandler("stop", stop_chat))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)

    print("🚀 Bot is polling...")
    # Start the Bot
    updater.start_polling(drop_pending_updates=True)

    # Run the bot until you send a signal to stop
    updater.idle()

# Run bot
if __name__ == "__main__":
    main()
