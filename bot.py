# bot.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import init_db, save_file, get_file, add_reaction, get_reactions
import asyncio
import threading
from flask import Flask

API_ID = 26438691
API_HASH = "b9a6835fa0eea6e9f8a87a320b3ab1ae"
BOT_TOKEN = "8031070707:AAEsIpxZCGtggUPzprlREbWA3aOF-cJb99g"

REQUIRED_CHANNELS = [
    "@BoxOffice_Animation",
    "@BoxOfficeMoviiie",
    "@BoxOffice_Irani",
    "@BoxOfficeGoftegu"
]

init_db()

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def check_user_membership(client, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in ["member", "creator", "administrator"]:
                return False
        except:
            return False
    return True

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
    link = f"https://t.me/{client.me.username}?start=file_{file_row_id}"
    markdown_link = f"[برای دانلود این فیلم کلیک کنید]({link})"
    await message.reply(f"✅ فایل با موفقیت آپلود شد!\n📥 {markdown_link}", parse_mode="markdown")

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("file_"):
            file_row_id = param.split("_")[1]
            if file_row_id.isdigit():
                is_member = await check_user_membership(client, message.from_user.id)
                if not is_member:
                    join_buttons = [[InlineKeyboardButton("عضو شدم ✅", callback_data=f"check_{file_row_id}")]]
                    for ch in REQUIRED_CHANNELS:
                        join_buttons.insert(0, [InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch.lstrip('@')}")])
                    await message.reply("برای دریافت فایل، ابتدا در کانال‌های زیر عضو شوید و سپس روی 'عضو شدم ✅' کلیک کنید:", reply_markup=InlineKeyboardMarkup(join_buttons))
                    return

                file_data = get_file(int(file_row_id))
                if file_data:
                    file_id, file_name, file_type = file_data
                    likes, dislikes = get_reactions(int(file_row_id))

                    caption = (
                        f"💙 سلام دوست عزیز!\n"
                        f"⚠️ این فایل فقط 30 ثانیه قابل دسترسی است.\n"
                        f"لطفاً آن را به پیوی خود بفرستید یا ذخیره کنید.\n\n"
                        f"📌 پیشنهاد: برای نمایش زیرنویس از MX Player استفاده کنید.\n\n"
                        f"👍 {likes} | 👎 {dislikes}"
                    )

                    buttons = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(f"👍 {likes}", callback_data=f"like_{file_row_id}"),
                            InlineKeyboardButton(f"👎 {dislikes}", callback_data=f"dislike_{file_row_id}")
                        ]
                    ])

                    try:
                        if file_type == "document":
                            sent_message = await message.reply_document(document=file_id, caption=caption, reply_markup=buttons)
                        elif file_type == "video":
                            sent_message = await message.reply_video(video=file_id, caption=caption, reply_markup=buttons)
                        else:
                            await message.reply("نوع فایل نامشخص است.")
                            return
                    except Exception as e:
                        await message.reply(f"خطا در ارسال فایل: {e}")
                        return

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

@app.on_callback_query()
async def handle_reaction(client, callback_query: CallbackQuery):
    data = callback_query.data
    if data.startswith("like_") or data.startswith("dislike_"):
        action, file_row_id = data.split("_")
        if file_row_id.isdigit():
            add_reaction(int(file_row_id), action)
            likes, dislikes = get_reactions(int(file_row_id))
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"👍 {likes}", callback_data=f"like_{file_row_id}"),
                    InlineKeyboardButton(f"👎 {dislikes}", callback_data=f"dislike_{file_row_id}")
                ]
            ])
            try:
                await callback_query.message.edit_reply_markup(reply_markup=buttons)
            except:
                pass
        await callback_query.answer("ثبت شد.", show_alert=False)

    elif data.startswith("check_"):
        file_row_id = data.split("_")[1]
        is_member = await check_user_membership(client, callback_query.from_user.id)
        if is_member:
            await start(client, callback_query.message)
        else:
            await callback_query.answer("هنوز عضو همه کانال‌ها نیستی!", show_alert=True)

# اجرای Flask روی پورت 10000 برای Render
fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running."

def run_web():
    fake_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

app.run()
