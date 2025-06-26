from pyrogram import Client, filters
from database import init_db, save_file, get_file
import asyncio
from flask import Flask
import threading

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

init_db()

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    await message.reply("🎬 خوش آمدی به باکس‌آفیس! برای تو بهترین فیلم‌ها رو داریم! 🍿✨")
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
    await message.reply(f"✅ فایل با موفقیت آپلود و ذخیره شد.
📥 لینک دانلود:
{link}")

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
                    sent_message = await message.reply_video(
                        video=file_id,
                        caption=(
                            "❗ فایل پس از **دو دقیقه** حذف خواهد شد.
"
                            "حتماً ابتدا **دانلود** کنید.

"
                            "📌 برای پخش زیرنویس، از **MX Player** استفاده کنید."
                        )
                    )
                    await asyncio.sleep(120)
                    await sent_message.delete()
                    await message.delete()
                    return
                else:
                    await message.reply("❌ فایل پیدا نشد.")
                    return
        await message.reply("❌ پارامتر شروع نامعتبر است.")
    else:
        await message.reply("سلام! لطفاً لینک را با پارامتر صحیح باز کنید.
مثال:
/start file_1")

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

app.run()
