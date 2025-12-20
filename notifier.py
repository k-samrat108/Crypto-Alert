from telegram import Bot
from config import BOT_TOKEN, CHANNEL_ID

bot = Bot(token=BOT_TOKEN)

async def send_alert(text, user_id):
    await bot.send_message(chat_id=user_id, text=text)
    await bot.send_message(chat_id=CHANNEL_ID, text=text)
