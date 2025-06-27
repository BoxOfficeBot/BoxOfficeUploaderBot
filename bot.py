from pyrogram import Client, filters
from database import init_db, save_file, get_file
import asyncio
import threading
from flask import Flask

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

init_db()

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

    file_row_id = save_file(file_id, file_name)
    link = f"https://t.me/{client.me.username}?start=file_{file_row_id}"
    await message.reply(f"✅ فایل با موفقیت آپلود شد!\n📥 لینک دانلود:\n{link}")

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
                        "لطفاً آن را به پیوی خود بفرستید یا ذخیره کنید.\n\n"
                        "📌 پیشنهاد: برای نمایش زیرنویس از MX Player استفاده کنید."
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

# اجرای Flask روی پورت 10000 برای Render
fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

# اجرای Flask در یک Thread جدا
threading.Thread(target=run_web).start()

# اجرای Pyrogram
app.run()
