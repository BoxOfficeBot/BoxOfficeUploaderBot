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
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
        file_type = "video"
    else:
        await message.reply("فایل باید ویدیو یا سند باشد.")
        return

    file_row_id = save_file(file_id, file_name, file_type)
    bot_info = await client.get_me()
    username = bot_info.username
    link = f"https://t.me/{username}?start=file_{file_row_id}"
    await message.reply(f"✅ فایل با موفقیت آپلود شد!\n📥 لینک دانلود:\n{link}")

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user = message.from_user
    name = user.first_name or "کاربر عزیز"
    username = user.username or "کاربر"

    # پیام خوش‌آمدگویی با اسم یا یوزرنیم
    welcome_text = f"""
🎉 خوش اومدی {name} عزیز! 💖

🔐 این ربات بهت امکان میده ویدیوها و فایل‌هاتو خیلی راحت و امن دریافت کنی!
📦 لینک‌هایی که می‌گیری فقط 30 ثانیه اعتبار دارن ⏳

⚡️ آماده‌ای؟ بزن بریم! 🚀
"""
    await message.reply_photo(
        photo="https://telegra.ph/file/6b9a31dd77ad04e3b84ef.jpg",
        caption=welcome_text
    )

    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("file_"):
            file_row_id = param.split("_")[1]
            file_data = get_file(file_row_id)
            if file_data:
                file_id, file_name, file_type = file_data
                file_caption = file_name or "📁 فایل شما آماده است."
                try:
                    if file_type == "document":
                        sent_message = await message.reply_document(document=file_id, caption=file_caption)
                    elif file_type == "video":
                        sent_message = await message.reply_video(video=file_id, caption=file_caption)
                    else:
                        await message.reply("نوع فایل نامشخص است.")
                        return
                except Exception as e:
                    await message.reply(f"خطا در ارسال فایل: {e}")
                    return

                warning_msg = await message.reply(
                    "⏳ فقط 30 ثانیه وقت داری! 😱\n📥 سریع فایل رو ذخیره کن یا بفرست به خودت!\n🔥 بعدش پاک میشه و از دستت میره! 🚫"
                )

                await asyncio.sleep(30)
                await sent_message.delete()
                await warning_msg.delete()
                await message.delete()
                return
            else:
                await message.reply("❌ فایل پیدا نشد.")
                return
        await message.reply("❌ پارامتر شروع نامعتبر است.")
    else:
        await message.reply("سلام رفیق! 🤗\nلطفاً لینک رو درست باز کن تا فایلتو بگیری.\nمثال:\n/start file_1")

fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()
app.run()
