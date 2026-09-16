import os
import re
import random
import asyncio
import logging
import sqlite3
import urllib.parse
import requests
import yt_dlp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8882604388:AAEwkBLMbtlKtWRVD-xNWrDE_t5SdzJQ4kM"
ADMIN_ID = 7454712269
ADMIN_USERNAME = "Md_atiqul_islam0"

PROXIES_LIST = [
    "http://185.199.229.156:7492", "http://185.199.228.220:7300",
    "http://185.199.231.45:8382", "http://188.166.205.155:3128",
    "http://159.65.133.175:3128", "http://165.225.208.84:80"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Android 10; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== ডাটাবেজ ====================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ==================== কীবোর্ড ====================
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎬 TikTok Download"), KeyboardButton("📘 Facebook Download")],
        [KeyboardButton("🔴 YouTube Download"), KeyboardButton("📸 Instagram Download")],
        [KeyboardButton("🖼️ Image Link Creator"), KeyboardButton("🔳 QR Code Generator")],
        [KeyboardButton("🎵 Audio Only (MP3)"), KeyboardButton("🔗 Web Direct Link")],
        [KeyboardButton("👨‍💻 Admin Support / Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ১০টি পিকচার আপলোড এপিআই ====================
def upload_image_multi(file_path):
    # API 1: Catbox
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=8)
            if r.status_code == 200 and r.text.startswith("http"):
                return r.text.strip()
    except Exception: pass

    # API 2: FreeImageHost
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://freeimage.host/api/1/upload", data={"key": "6d207e02198a847aa98d0a2a901485a5"}, files={"source": f}, timeout=8)
            res = r.json()
            if res.get("status_code") == 200:
                return res["image"]["url"]
    except Exception: pass

    # API 3: TmpFiles
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=8)
            res = r.json()
            if res.get("status") == "success":
                return res["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception: pass

    # API 4: Litterbox
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://litterbox.catbox.moe/resources/internals/api.php", data={"reqtype": "fileupload", "time": "1h"}, files={"fileToUpload": f}, timeout=8)
            if r.status_code == 200 and r.text.startswith("http"):
                return r.text.strip()
    except Exception: pass

    # API 5: ImgBB Backup
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://api.imgbb.com/1/upload?key=6d207e02198a847aa98d0a2a901485a5", files={"image": f}, timeout=8)
            res = r.json()
            if res.get("success"):
                return res["data"]["url"]
    except Exception: pass

    return None

# ==================== ৫টি QR কোড এপিআই ====================
def generate_qr_multi_api(text_data):
    encoded = urllib.parse.quote(text_data)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={encoded}"

# ==================== স্টার্ট ও অন্য হ্যান্ডলার ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data['mode'] = 'video'
    
    welcome_msg = (
        "🌟 **আমাদের পাওয়ারফুল অল-ইন-ওয়ান ডাউনলোডার বটে আপনাকে স্বাগতম!** 🌟\n\n"
        "⚡ **সার্ভিসসমূহ:**\n"
        "• 🎬 **TikTok, FB, YT, Insta** ফাস্ট ডাউনলোডার\n"
        "• 🖼️ **Image To Direct Link** জেনারেটর\n"
        "• 🔳 **QR Code Generator**\n"
        "• 🎵 **MP3 Audio Downloader**\n\n"
        "👇 *নিচের কীবোর্ড থেকে যেকোনো একটি ফিচার সিলেক্ট করুন:*"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ফটো হ্যান্ডলার (ছবি অটো-ডিলিট লজিক সহ)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    status_msg = await update.message.reply_text("⏳ ছবি প্রসেস করে ডাইরেক্ট লিংক তৈরি করা হচ্ছে...")

    user_photo_msg_id = update.message.message_id
    photo_file = await update.message.photo[-1].get_file()
    temp_path = f"img_{user_photo_msg_id}.jpg"
    
    try:
        await photo_file.download_to_drive(temp_path)
        loop = asyncio.get_event_loop()
        direct_link = await loop.run_in_executor(None, upload_image_multi, temp_path)

        if direct_link:
            res_text = (
                "✅ **Image Direct Link Created!**\n\n"
                f"`{direct_link}`"
            )
            # ১. আগের পাঠানো ফটো ডিলিট
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_photo_msg_id)
            except Exception: pass

            # ২. প্রসেসিং স্ট্যাটাস ডিলিট করে নতুন লিংক পাঠানো
            await status_msg.delete()
            await context.bot.send_message(chat_id=update.effective_chat.id, text=res_text, parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ এপিআই সার্ভার ব্যস্ত! আবার চেষ্টা করুন।")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# টেক্সট ও ডাউনলোড হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)

    if text in ["🎬 TikTok Download", "📘 Facebook Download", "🔴 YouTube Download", "📸 Instagram Download"]:
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ ভিডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক পাঠান:", reply_markup=get_main_keyboard())
        return
    elif text == "🖼️ Image Link Creator":
        context.user_data['mode'] = 'image'
        await update.message.reply_text("📸 যেকোনো ফটো পাঠান, বট ফটোটি ডিলিট করে ডাইরেক্ট লিংক দিয়ে দেবে।", reply_markup=get_main_keyboard())
        return
    elif text == "🔳 QR Code Generator":
        context.user_data['mode'] = 'qrcode'
        await update.message.reply_text("🔳 যেকোনো লিংক বা লেখা পাঠান, বট QR কোড তৈরি করে দেবে।", reply_markup=get_main_keyboard())
        return
    elif text == "🎵 Audio Only (MP3)":
        context.user_data['mode'] = 'audio'
        await update.message.reply_text("🎵 MP3 অডিও মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_main_keyboard())
        return
    elif text == "🔗 Web Direct Link":
        context.user_data['mode'] = 'weblink'
        await update.message.reply_text("🔗 Web Stream Link মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_main_keyboard())
        return
    elif text == "👨‍💻 Admin Support / Help":
        support_msg = (
            "👨‍💻 **Admin & Developer Support**\n\n"
            f"👤 **Admin User:** @{ADMIN_USERNAME}\n"
            f"💬 **Direct Chat:** https://t.me/{ADMIN_USERNAME}"
        )
        await update.message.reply_text(support_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return

    mode = context.user_data.get('mode', 'video')

    # QR Code প্রসেসিং
    if mode == 'qrcode' or (not text.startswith("http") and mode != 'weblink'):
        if mode == 'qrcode':
            qr_img_url = generate_qr_multi_api(text)
            await update.message.reply_photo(photo=qr_img_url, caption=f"🔳 **QR Code Generated!**\n\n`{text}`", parse_mode="Markdown")
            return
        elif not text.startswith("http"):
            await update.message.reply_text("❌ অনুগ্রহ করে সঠিক ভিডিও লিংক বা ছবি পাঠান।", reply_markup=get_main_keyboard())
            return

    url = text
    status_msg = await update.message.reply_text("🔍 লিঙ্ক চেক করা হচ্ছে...")
    selected_ua = random.choice(USER_AGENTS)

    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': selected_ua,
        'nocheckcertificate': True
    }

    filename = None
    try:
        loop = asyncio.get_event_loop()
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, fetch_info)
        duration = info.get('duration', 0)

        if duration and duration > 600:
            await status_msg.edit_text("❌ ভিডিওটি ১০ মিনিটের বেশি বড়!")
            return

        if mode == 'weblink':
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                direct_url = info['formats'][-1].get('url')

            if direct_url:
                await status_msg.edit_text(f"🔗 **Web Stream Link:**\n\n`{direct_url}`", parse_mode="Markdown")
            else:
                await status_msg.edit_text("❌ ওয়েব লিংক জেনারেট করা সম্ভব হয়নি।")
            return

        await status_msg.edit_text("⬇️ Downloading...\n`[▓▓▓▓▓░░░░░] 50%`", parse_mode="Markdown")
        file_prefix = f"dl_{update.message.message_id}"
        
        ydl_download_opts = {
            'format': 'best[ext=mp4]/best' if mode == 'video' else 'bestaudio/best',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'quiet': True,
            'max_filesize': 50 * 1024 * 1024, # ৫০ এমবির বেশি ফাইল ব্লক
            'user_agent': selected_ua,
            'nocheckcertificate': True
        }

        def download_file():
            with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                d_info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(d_info)

        filename = await loop.run_in_executor(None, download_file)

        await status_msg.edit_text("📤 Telegram-এ সেন্ড করা হচ্ছে...")

        with open(filename, 'rb') as f:
            if mode == 'audio':
                await update.message.reply_audio(audio=f, caption="🎵 Downloaded via Auto Bot")
            else:
                await update.message.reply_video(video=f, caption="🎥 Downloaded via Auto Bot")

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ ভিডিও ডাউনলোড করতে সমস্যা হয়েছে। ফেসবুক প্রাইভেট ভিডিও বা ৫০MB-র বেশি বড় ফাইল ডাউনলোড করা সম্ভব নয়।")
    finally:
        # মেমোরি ফিক্স: ফাইলটি টেলিগ্রামে পাঠানোর পর ব্যাকএন্ড থেকে ডিলিট
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception: pass

# ==================== এডমিন কমান্ড ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    total_users = get_users_count()
    admin_text = f"👑 **Admin Panel**\n\n📊 **Total Users:** {total_users}\n\n📢 **Broadcast:**\n`/broadcast আপনার বার্তা`"
    await update.message.reply_text(admin_text, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ মেসেজ লিখুন! উদাহরণ:\n`/broadcast আপনার নোটিশ`", parse_mode="Markdown")
        return

    broadcast_text = " ".join(context.args)
    users = get_all_users()
    success = 0

    status = await update.message.reply_text("📢 ব্রডকাস্ট পাঠানো শুরু হয়েছে...")

    for u_id in users:
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 **Notice:**\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass

    await status.edit_text(f"✅ ব্রডকাস্ট সম্পন্ন!\nমোট {success}/{len(users)} জন ইউজার মেসেজ পেয়েছে।")

# ==================== মেইন ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
            
