import os
from pyrogram import Client, filters
from pyrogram.types import Message
from database import init_db, save_file, get_file, schedule_file
from flask import Flask
from datetime import datetime
import pytz

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

init_db()
bot = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@bot.on_message(filters.document & filters.private)
async def handle_file(client: Client, message: Message):
    await message.reply("لطفاً یک شناسه یکتا برای این فایل ارسال کنید:")
    file_msg = message

    @bot.on_message(filters.text & filters.private)
    async def get_unique_id(_, msg):
        unique_id = msg.text.strip()
        file_id = file_msg.document.file_id
        caption = file_msg.caption or ""
        file_type = "document"
        save_file(file_id, caption, file_type, unique_id)
        await msg.reply("✅ فایل با موفقیت ذخیره شد!")

        bot.remove_handler(get_unique_id)

@bot.on_message(filters.command("get") & filters.private)
async def send_file(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("لطفاً شناسه یکتا را وارد کنید. مثال: /get ID123")

    unique_id = message.command[1]
    file_data = get_file(unique_id)

    if not file_data:
        return await message.reply("فایلی با این شناسه پیدا نشد.")

    await message.reply_document(
        document=file_data['file_id'],
        caption=file_data['caption']
    )

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

bot.start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
