import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import save_file, get_files_by_film_id
from urllib.parse import quote_plus

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAHgOK59zZxMTMCoRHj32awnkXHbk7qhra8"
ADMIN_ID = 7872708405  # ادمین خودت

app = Client("BoxOfficeUploaderbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

upload_data = {}  # ذخیره اطلاعات موقت آپلود توسط ادمین

CHANNELS = [
    "@BoxOffice_Irani",
    "@BoxOfficeMoviiie",
    "@BoxOffice_Animation",
    "@BoxOfficeGoftegu",
]

async def check_membership(client, user_id):
    for channel in CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status in ("kicked", "left"):
                return False, channel
        except Exception:
            return False, channel
    return True, None

@app.on_message(filters.private & filters.user(ADMIN_ID) & filters.video)
async def video_received(client, message):
    user_id = message.from_user.id
    upload_data[user_id] = {
        "video_file_id": message.video.file_id,
        "step": "awaiting_film_id"
    }
    await message.reply("✅ ویدئو دریافت شد.\nلطفاً شناسه عددی فیلم را وارد کنید:")

@app.on_message(filters.private & filters.user(ADMIN_ID) & filters.text)
async def text_received(client, message):
    user_id = message.from_user.id

    if user_id not in upload_data:
        await message.reply("لطفاً ابتدا ویدئو ارسال کنید.")
        return

    data = upload_data[user_id]

    if data.get("step") == "awaiting_film_id":
        film_id = message.text.strip()
        data["film_id"] = film_id
        data["step"] = "awaiting_caption"
        await message.reply("لطفاً کپشن کوتاه برای فیلم وارد کنید:")
        return

    if data.get("step") == "awaiting_caption":
        caption = message.text.strip()
        data["caption"] = caption
        data["step"] = "awaiting_quality"
        await message.reply("لطفاً کیفیت فیلم را وارد کنید (مثلاً 360p، 720p):")
        return

    if data.get("step") == "awaiting_quality":
        quality = message.text.strip()
        data["quality"] = quality

        # ذخیره در دیتابیس
        save_file(
            film_id=data["film_id"],
            file_id=data["video_file_id"],
            caption=data["caption"],
            quality=data["quality"]
        )

        # ساختن لینک deep link
        deep_link = f"https://t.me/{(await client.get_me()).username}?start={data['film_id']}"

        await message.reply(
            f"✅ فایل با شناسه فیلم {data['film_id']} با کیفیت {quality} ذخیره شد.\n\n"
            f"🔗 لینک اشتراک برای این فیلم:\n{deep_link}"
        )

        upload_data.pop(user_id)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    args = message.text.split()
    user_id = message.from_user.id

    if len(args) == 2:
        film_id = args[1]

        # چک عضویت کانال‌ها
        is_member, missing_channel = await check_membership(client, user_id)
        if not is_member:
            await message.reply(
                f"⚠️ لطفاً ابتدا عضو کانال {missing_channel} شوید و دوباره تلاش کنید.\n"
                f"لینک کانال: https://t.me/{missing_channel.lstrip('@')}"
            )
            return

        files = get_files_by_film_id(film_id)

        if not files:
            await message.reply("❌ هیچ فایلی با این شناسه یافت نشد.")
            return

        await message.reply(f"🎬 فیلم با شناسه {film_id} پیدا شد. در حال ارسال فایل‌ها...")

        sent_messages = []

        for file in files:
            caption = f"{file['caption']} | کیفیت: {file['quality']}"
            sent = await client.send_video(message.chat.id, file['file_id'], caption=caption)
            sent_messages.append(sent)

        warning_msg = await message.reply(
            "⚠️ توجه: فایل‌ها پس از ۳۰ ثانیه حذف خواهند شد. لطفاً در این مدت آن‌ها را ذخیره کنید."
        )
        sent_messages.append(warning_msg)

        # حذف پیام‌ها و فایل‌ها بعد از ۳۰ ثانیه
        await asyncio.sleep(30)
        for msg in sent_messages:
            try:
                await msg.delete()
            except:
                pass

    else:
        # استارت معمولی
        await message.reply(
            "سلام!\nربات اشتراک فایل فیلم.\n"
            "لینک دریافت فایل‌ها را از کانال یا ادمین دریافت کنید."
        )


if __name__ == "__main__":
    print("✅ ربات با موفقیت اجرا شد و منتظر پیام‌هاست...")
    app.run()
