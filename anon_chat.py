import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
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

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Handle /start command
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_gender[user_id] = "ask"
    await message.reply("Welcome to Anonymous Chat!\nWhat is your gender? (Male/Female/Other)")

# Handle plain text messages
@dp.message_handler(content_types=['text'])
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id in user_gender and user_gender[user_id] == "ask":
        if text in ["male", "female", "other"]:
            user_gender[user_id] = text
            user_pref_gender[user_id] = "ask"
            await message.reply("Who do you want to chat with? (Male/Female/Any)")
        else:
            await message.reply("Please choose: Male, Female or Other")
        return

    if user_id in user_pref_gender and user_pref_gender[user_id] == "ask":
        if text in ["male", "female", "any"]:
            user_pref_gender[user_id] = text
            await message.reply("Done! Use /search to find a chat partner.")
        else:
            await message.reply("Please choose: Male, Female, or Any.")
        return

    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if partner_id:
            await bot.send_message(chat_id=partner_id, text=message.text)

# Handle /search command
@dp.message_handler(commands=['search'])
async def search(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        await message.reply("You're already chatting. Use /next to skip.")
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

            await bot.send_message(chat_id=user_id, text="Connected! Say hi!")
            await bot.send_message(chat_id=partner_id, text="Connected! Say hi!")
            return

    waiting_users.append(user_id)
    await message.reply("Waiting for a partner...")

# Handle /next command
@dp.message_handler(commands=['next'])
async def next_chat(message: types.Message):
    user_id = message.from_user.id
    partner_id = active_chats.pop(user_id, None)

    if partner_id:
        active_chats.pop(partner_id, None)
        await bot.send_message(chat_id=partner_id, text="Your partner left. Use /search to find someone new.")

    await search(message)

# Handle /stop command
@dp.message_handler(commands=['stop'])
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            await bot.send_message(chat_id=partner_id, text="Your partner left the chat.")

    await message.reply("You left the chat. Use /search to find someone else.")

# Main function
async def main():
    print("🔧 Setting up bot application...")
    print("🚀 Bot is polling...")
    
    # Start polling
    await dp.start_polling(skip_updates=True)

# Run bot
if __name__ == "__main__":
    asyncio.run(main())
