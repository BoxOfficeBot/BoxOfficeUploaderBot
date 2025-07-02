# directory: BoxOfficeUploaderBot

# 1. requirements.txt
'''
pyrogram
Flask
APScheduler
tgcrypto
pytz
pyaes==1.6.1
pysocks==1.7.1
'''

# 2. database.py
from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["BoxOffice"]
collection = db["files"]

def init_db():
    db.command("ping")

def save_file(file_id, caption, file_type, unique_id, schedule_time=None, channel_id=None):
    collection.insert_one({
        "file_id": file_id,
        "caption": caption,
        "file_type": file_type,
        "unique_id": unique_id,
        "schedule_time": schedule_time,
        "channel_id": channel_id,
        "created_at": datetime.utcnow()
    })

def get_file(unique_id):
    return collection.find_one({"unique_id": unique_id})

def schedule_file(unique_id, schedule_time, channel_id):
    collection.update_one(
        {"unique_id": unique_id},
        {"$set": {"schedule_time": schedule_time, "channel_id": channel_id}}
    )

def get_scheduled_files():
    return list(collection.find({"schedule_time": {"$ne": None}}))


# 3. scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pyrogram import Client
from database import get_scheduled_files
import asyncio
import pytz

scheduler = BackgroundScheduler()

async def send_scheduled_files(bot):
    files = get_scheduled_files()
    now = datetime.now(pytz.utc)
    for file in files:
        if file['schedule_time'] <= now:
            try:
                await bot.send_document(
                    chat_id=file['channel_id'],
                    document=file['file_id'],
                    caption=file['caption']
                )
            except Exception as e:
                print("Error sending scheduled file:", e)

scheduler.add_job(lambda: asyncio.run(send_scheduled_files(Client("bot"))), 'interval', minutes=1)
scheduler.start()


# 4. bot.py
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


# 5. .env (locally, do NOT push this to GitHub)
'''
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
MONGO_URI=mongodb+srv://smilymeh:M@hdi1985!@cluster0.ve2f0zq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
PORT=10000
'''


# نکته:
# در render.com باید این متغیرها رو تو بخش Environment اضافه کنی نه داخل فایل .env واقعی
