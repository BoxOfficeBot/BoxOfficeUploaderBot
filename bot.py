from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, save_file, get_file, schedule_file, get_scheduled_files
import asyncio
import threading
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
import pytz

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"
ADMIN_ID = 5109533656

CHANNELS = {
    "🎬 BoxOffice Irani": -1002422139602,
    "🎞️ BoxOffice Moviiie": -1002601782167,
    "🐉 BoxOffice Animation": -1002573288143
}

init_db()
app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = BackgroundScheduler(timezone="Europe/Berlin")
scheduler.start()


@app.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ فقط ادمین مجاز به آپلود فایل است.")
        return

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

    # ✅ اصلاح‌شده: نمایش لینک به صورت کامل
    await message.reply(f"✅ فایل با موفقیت آپلود شد!\n📥 لینک دانلود:\n{link}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"channel_{file_row_id}_{chat_id}")]
        for name, chat_id in CHANNELS.items()
    ])
    await message.reply("📢 لطفاً کانالی که می‌خوای فایل توش منتشر بشه رو انتخاب کن:", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^channel_(\d+)_(\-\d+)$"))
async def select_channel(client, callback_query):
    file_row_id, chat_id = map(int, callback_query.data.split("_")[1:])
    await callback_query.message.edit("🕐 لطفاً زمان ارسال فایل رو به صورت `YYYY-MM-DD HH:MM` وارد کن:", parse_mode="markdown")
    app.db_state = {callback_query.from_user.id: {"file_id": file_row_id, "chat_id": chat_id}}


@app.on_message(filters.private & filters.text)
async def set_schedule(client, message):
    state = getattr(app, "db_state", {}).get(message.from_user.id)
    if not state:
        return

    try:
        run_at = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
        run_at = pytz.timezone("Europe/Berlin").localize(run_at)
    except Exception:
        await message.reply("❌ فرمت زمان اشتباهه. لطفاً به صورت `YYYY-MM-DD HH:MM` بنویس.", parse_mode="markdown")
        return

    file_data = get_file(state["file_id"])
    if not file_data:
        await message.reply("❌ فایل پیدا نشد.")
        return

    schedule_file(state["file_id"], run_at.isoformat(), state["chat_id"])

    scheduler.add_job(
        func=send_scheduled_file,
        trigger="date",
        run_date=run_at,
        args=[state["file_id"]],
        id=f"job_{state['file_id']}"
    )

    await message.reply("📅 زمان‌بندی با موفقیت انجام شد ✅")
    del app.db_state[message.from_user.id]


async def send_scheduled_file(file_id):
    file_data = get_file(file_id)
    if not file_data:
        return
    file_id, file_name, file_type, schedule_time, channel_id = file_data
    caption = f"🎬 {file_name}"
    try:
        if file_type == "document":
            await app.send_document(channel_id, document=file_id, caption=caption)
        elif file_type == "video":
            await app.send_video(channel_id, video=file_id, caption=caption)
    except Exception as e:
        print(f"خطا در ارسال فایل برنامه‌ریزی‌شده: {e}")


fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."


def run_web():
    fake_app.run(host="0.0.0.0", port=10000)


threading.Thread(target=run_web).start()
app.run()
