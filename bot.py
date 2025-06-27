from pyrogram import Client, filters
from database import init_db, save_file, get_file
import asyncio

# اطلاعات API
API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

# شروع دیتابیس
init_db()

# راه‌اندازی بات
app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# هندل کردن آپلود فایل
@app.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "file"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
    else:
        await message.reply("فایل باید ویدیو یا سند باشد.")
        return

    # ذخیره در دیتابیس
    file_row_id = save_file(file_id, file_name)

    # ساخت لینک
    link = f"https://t.me/{client.me.username}?start=file_{file_row_id}"

    await message.reply(
        f"✅ فایل با موفقیت آپلود شد!\n"
        f"📥 برای دریافت فایل روی لینک زیر کلیک کنید:\n\n{link}"
    )

# هندل کردن start
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("file_"):
            file_row_id = param.split("_")[1]
            if file_row_id.isdigit():
                file_data = get_file(int(file_row_id))
                if file_data:
                    file_id, file_name = file_data
                    caption = (
                        "💙 سلام دوست عزیز!\n"
                        "⚠️ این فایل فقط 30 ثانیه قابل دسترسی است.\n"
                        "حتماً به پیوی خود فوروارد کنید یا ذخیره کنید.\n\n"
                        "📌 برای نمایش زیرنویس از MX Player استفاده کنید."
                    )

                    try:
                        sent_message = await message.reply_document(document=file_id, caption=caption)
                    except ValueError:
                        sent_message = await message.reply_video(video=file_id, caption=caption)

                    await asyncio.sleep(30)
                    await sent_message.delete()
                    await message.delete()
                    return
                else:
                    await message.reply("❌ فایل پیدا نشد.")
                    return
        await message.reply("❌ پارامتر شروع نامعتبر است.")
    else:
        await message.reply("سلام! لطفاً لینک را با پارامتر صحیح باز کنید.\nمثال:\n/start file_1")

# اجرای ربات
app.run()

# Fake Web Server برای Render
from flask import Flask
import threading

fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()
