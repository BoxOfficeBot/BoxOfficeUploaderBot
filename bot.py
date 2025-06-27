from pyrogram import Client, filters
from database import init_db, save_file, get_file
import asyncio
from flask import Flask
import threading

# اطلاعات ربات
API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

# آماده‌سازی دیتابیس
init_db()

# ساخت کلاینت ربات
app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# هندل آپلود فایل
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

    # دریافت یوزرنیم ربات
    bot_user = await client.get_me()
    link = f"https://t.me/{bot_user.username}?start=file_{file_row_id}"

    # ارسال لینک دانلود
    await message.reply(
        f"✅ فایل با موفقیت آپلود و ذخیره شد.\n"
        f"🔗 لینک دریافت فایل:\n{link}"
    )


# هندل دستور start
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
                        "⚠️ توجه کنید که این فایل فقط به مدت ۳۰ ثانیه قابل دسترسی است.\n"
                        "لطفاً آن را برای خود فوروارد کرده و ذخیره کنید ❤️\n\n"
                        "📌 برای پخش زیرنویس، از MX Player استفاده کنید."
                    )
                    if file_id.startswith("BAAC") or file_id.startswith("CAAC"):
                        sent_message = await message.reply_document(document=file_id, caption=caption)
                    else:
                        sent_message = await message.reply_video(video=file_id, caption=caption)

                    await asyncio.sleep(30)
                    await sent_message.delete()
                    await message.delete()
                    return
                else:
                    await message.reply("❌ فایل مورد نظر یافت نشد.")
                    return
        await message.reply("❌ پارامتر شروع نامعتبر است.")
    else:
        await message.reply(
            "سلام! لطفاً لینک را با پارامتر درست باز کنید.\n"
            "مثال:\n/start file_1"
        )


# اجرای ربات
app.start()


# سرور فیک برای Render تا پورت باز باشد
fake_app = Flask(__name__)

@fake_app.route("/")
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# اجرای دائمی Pyrogram
app.idle()
