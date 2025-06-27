from pyrogram import Client, filters
from database import init_db, save_file, get_file
import asyncio
from flask import Flask
import threading

# تنظیمات ربات
API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"
ADMIN_ID = 7872708405  # فقط ادمین اجازه آپلود دارد

# دیتابیس
init_db()

# ربات
app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ فقط ادمین می‌تونه فایل آپلود کنه.")
        return

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "file"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
    else:
        await message.reply("❌ فقط فایل ویدیو یا سند قابل قبول است.")
        return

    file_row_id = save_file(file_id, file_name)
    
    # ⚠️ اینجا خیلی مهمه: باید خود `client.me.username` رو با await فراخوانی کنیم
    me = await client.get_me()
    link = f"https://t.me/{me.username}?start=file_{file_row_id}"

    await message.reply(
        f"✅ فایل با موفقیت آپلود شد!\n"
        f"📥 لینک اختصاصی برای اشتراک:\n👉 {link}"
    )

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
                        "⚠️ توجه کنید که بعد از 30 ثانیه حذف خواهد شد\n"
                        "لطفاً پیام(های) ارسالی را به پیوی خود فوروارد و ذخیره کنید ❤️\n\n"
                        "📌 برای نمایش زیرنویس‌ها از MX Player استفاده کنید."
                    )

                    if file_id.startswith("BAAC") or file_id.startswith("CAAC"):  # سند
                        sent_message = await message.reply_document(document=file_id, caption=caption)
                    else:
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
        await message.reply("سلام! لطفاً لینک فیلم را با فرمت صحیح باز کنید.\nمثال:\n/start file_1")

# Fake Flask app برای اجرای روی Render
fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# اجرای ربات
app.run()
