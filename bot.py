from pyrogram import Client, filters
import asyncio
import sqlite3

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

# راه‌اندازی اتصال به دیتابیس SQLite
conn = sqlite3.connect("films.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER UNIQUE,
    file_id TEXT,
    file_type TEXT,
    file_name TEXT
)
""")
conn.commit()

app = Client("BoxOfficeProBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def save_file(file_id, file_type, file_name, message_id):
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO films (message_id, file_id, file_type, file_name) VALUES (?, ?, ?, ?)",
            (message_id, file_id, file_type, file_name)
        )
        conn.commit()
        # دریافت id ردیف ذخیره شده
        row = cursor.execute("SELECT id FROM films WHERE message_id=?", (message_id,)).fetchone()
        if row:
            return row[0]
        else:
            return None
    except Exception as e:
        print("DB Save Error:", e)
        return None

@app.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        file_name = message.document.file_name
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
        file_name = message.video.file_name or "video.mp4"
    else:
        await message.reply("فایل باید ویدیو یا سند باشد.")
        return

    film_id = save_file(file_id, file_type, file_name, message.id)
    if not film_id:
        await message.reply("❌ خطا در ذخیره فایل.")
        return

    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start=file_{film_id}"

    await message.reply(
        f"💙 سلام دوست عزیز!\n"
        f"✅ فایل با موفقیت ذخیره شد!\n"
        f"برای دریافت فایل می‌توانید از لینک زیر استفاده کنید:\n\n"
        f"{link}\n\n"
        f"⚠️ توجه: فایل تنها ۳۰ ثانیه قابل دسترسی است و سپس حذف می‌شود.\n"
        f"لطفاً ابتدا دانلود و ذخیره کنید."
    )

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("file_"):
            film_id_str = param.split("_")[1]
            if film_id_str.isdigit():
                film_id = int(film_id_str)
                cursor.execute("SELECT file_id, file_type, file_name FROM films WHERE id=?", (film_id,))
                film = cursor.fetchone()
                if film:
                    file_id, file_type, file_name = film
                    caption = (
                        "💙 سلام دوست عزیز!\n"
                        "❗ این فیلم به مدت ۳۰ ثانیه برای شما ارسال می‌شود.\n"
                        "لطفاً ابتدا ذخیره کنید و سپس مشاهده کنید.\n"
                        "❤️ با تشکر از حمایت شما.\n\n"
                        "📌 برای نمایش زیرنویس‌ها از نرم‌افزار MX Player استفاده کنید."
                    )
                    if file_type == "video":
                        sent = await message.reply_video(video=file_id, caption=caption)
                    else:
                        sent = await message.reply_document(document=file_id, caption=caption)

                    await asyncio.sleep(30)
                    await sent.delete()
                    await message.delete()
                    return
                else:
                    await message.reply("❌ فیلم پیدا نشد.")
                    return
        await message.reply("❌ پارامتر نامعتبر است.")
    else:
        await message.reply("سلام! لطفاً لینک فیلم را با فرمت صحیح وارد کنید.\nمثال:\n/start file_1")

app.run()
