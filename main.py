import os
import re
import random
import asyncio
import logging
import sqlite3
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

# ২০টি ফ্রি অ্যানোনিমাস প্রক্সি তালিকা (ভিডিও/অডিও ডাউনলোড ব্যাকআপের জন্য)
PROXIES_LIST = [
    "http://185.199.229.156:7492", "http://185.199.228.220:7300",
    "http://185.199.231.45:8382", "http://188.166.205.155:3128",
    "http://159.65.133.175:3128", "http://165.225.208.84:80",
    "http://165.225.222.241:80", "http://138.68.60.8:8080",
    "http://51.159.66.10:80", "http://51.158.123.35:8888",
    "http://163.172.31.28:8888", "http://51.15.242.200:8888",
    "http://51.158.106.54:8888", "http://163.172.48.117:8888",
    "http://51.15.166.107:8888", "http://198.51.100.1:8080",
    "http://203.0.113.195:80", "http://192.0.2.146:3128",
    "http://185.220.101.5:80", "http://185.220.101.7:80"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
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

# ==================== মেইন কীবোর্ড ====================
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎬 TikTok Download"), KeyboardButton("📘 Facebook Download")],
        [KeyboardButton("🔴 YouTube Download"), KeyboardButton("📸 Instagram Download")],
        [KeyboardButton("🖼️ Image Link Creator"), KeyboardButton("🎵 Audio Only (MP3)")],
        [KeyboardButton("🔗 Web Direct Link")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ১০টি ইমেজ আপলোড এপিআই ====================
def upload_image_10_apis(file_path):
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

    # API 5: File.io
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://file.io", files={"file": f}, timeout=8)
            res = r.json()
            if res.get("success"):
                return res.get("link")
    except Exception: pass

    # API 6: Pixeldrain
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://pixeldrain.com/api/file", files={"file": f}, timeout=8)
            res = r.json()
            if res.get("success"):
                return f"https://pixeldrain.com/api/file/{res.get('id')}"
    except Exception: pass

    # API 7: GoFile
    try:
        srv_req = requests.get("https://api.gofile.io/getBestServer", timeout=5).json()
        if srv_req.get("status") == "ok":
            srv = srv_req["data"]["server"]
            with open(file_path, 'rb') as f:
                r = requests.post(f"https://{srv}.gofile.io/uploadFile", files={"file": f}, timeout=8)
                res = r.json()
                if res.get("status") == "ok":
                    return res["data"]["downloadPage"]
    except Exception: pass

    # API 8: ImgBB Backup
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://api.imgbb.com/1/upload?key=6d207e02198a847aa98d0a2a901485a5", files={"image": f}, timeout=8)
            res = r.json()
            if res.get("success"):
                return res["data"]["url"]
    except Exception: pass

    # API 9: Pomf
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://pomf.cat/upload.php", files={"files[]": f}, timeout=8)
            res = r.json()
            if res.get("success"):
                return f"https://a.pomf.cat/{res['files'][0]['url']}"
    except Exception: pass

    # API 10: Dappnode
    try:
        with open(file_path, 'rb') as f:
            r = requests.post("https://ipfs.dappnode.io/api/v0/add", files={"file": f}, timeout=8)
            res = r.json()
            if "Hash" in res:
                return f"https://ipfs.io/ipfs/{res['Hash']}"
    except Exception: pass

    return None

# ==================== হ্যান্ডলারস ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data['mode'] = 'video'
    
    text = (
        "👋 **স্বাগতম!**\n\n"
        "ভিডিও/অডিও ডাউনলোড করতে লিংক পাঠান অথবা **🖼️ Image Link Creator** চাপ দিয়ে ছবি পাঠান।"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ফটো হ্যান্ডলার
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    status_msg = await update.message.reply_text("⏳ ছবি প্রসেস করা হচ্ছে এবং ১০টি এপিআই এর মাধ্যমে ডাইরেক্ট লিংক তৈরি হচ্ছে...")

    photo_file = await update.message.photo[-1].get_file()
    temp_path = f"img_{update.message.message_id}.jpg"
    await photo_file.download_to_drive(temp_path)

    loop = asyncio.get_event_loop()
    direct_link = await loop.run_in_executor(None, upload_image_10_apis, temp_path)

    # সার্ভার থেকে অটোমেটিক পিকচার ডিলিট
    if os.path.exists(temp_path):
        os.remove(temp_path)

    if direct_link:
        res_text = (
            "✅ **Image Direct Link Created!**\n\n"
            f"`{direct_link}`\n\n"
            "💡 এই লিংকটি যেকোনো ওয়েবসাইটে সরাসরি ব্যবহার করতে পারবেন।"
        )
        await status_msg.edit_text(res_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text("❌ সংযোগ ত্রুটি! অনুগ্রহ করে আবার চেষ্টা করুন।")

# টেক্সট ও ডাউনলোড হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)

    if text in ["🎬 TikTok Download", "📘 Facebook Download", "🔴 YouTube Download", "📸 Instagram Download"]:
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ ভিডিও ডাউনলোড মোড চালু হয়েছে। লিংক পাঠান:", reply_markup=get_main_keyboard())
        return
    elif text == "🖼️ Image Link Creator":
        context.user_data['mode'] = 'image'
        await update.message.reply_text("📸 যেকোনো ফটো পাঠান, বট ডাইরেক্ট ওয়েব লিংক তৈরি করে দেবে।", reply_markup=get_main_keyboard())
        return
    elif text == "🎵 Audio Only (MP3)":
        context.user_data['mode'] = 'audio'
        await update.message.reply_text("🎵 MP3 অডিও মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_main_keyboard())
        return
    elif text == "🔗 Web Direct Link":
        context.user_data['mode'] = 'weblink'
        await update.message.reply_text("🔗 Web Stream Link মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_main_keyboard())
        return

    url_pattern = re.compile(r'https?://[^\s]+')
    if not url_pattern.match(text):
        await update.message.reply_text("❌ অনুগ্রহ করে সঠিক ভিডিও লিংক বা ছবি পাঠান।", reply_markup=get_main_keyboard())
        return

    url = text
    mode = context.user_data.get('mode', 'video')

    status_msg = await update.message.reply_text("🔍 লিংক চেক করা হচ্ছে...")

    selected_proxy = random.choice(PROXIES_LIST)
    selected_ua = random.choice(USER_AGENTS)

    ydl_opts_info = {'quiet': True, 'no_warnings': True, 'user_agent': selected_ua, 'proxy': selected_proxy}

    try:
        loop = asyncio.get_event_loop()
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, fetch_info)
        duration = info.get('duration', 0)

        # ১০ মিনিটের বেশি হলে অটোমেটিক রিজেক্ট
        if duration and duration > 600:
            await status_msg.edit_text("❌ ভিডিওটি ১০ মিনিটের বেশি বড়! ১০ মিনিটের কম দৈর্ঘ্যের ভিডিও লিংক দিন।")
            return

        if mode == 'weblink':
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                direct_url = info['formats'][-1].get('url')

            if direct_url:
                await status_msg.edit_text(f"🔗 **Web Stream Link:**\n\n`{direct_url}`", parse_mode="Markdown")
            else:
                await status_msg.edit_text("❌ লিংক জেনারেট করা সম্ভব হয়নি।")
            return

        await status_msg.edit_text("⬇️ Downloading...\n`[░░░░░░░░░░] 0%`", parse_mode="Markdown")
        file_prefix = f"dl_{update.message.message_id}"
        
        ydl_download_opts = {
            'format': 'bestaudio/best' if mode == 'audio' else 'best[ext=mp4]/best',
            'outtmpl': f'{file_prefix}.%(ext)s' if mode == 'audio' else f'{file_prefix}.mp4',
            'quiet': True,
            'user_agent': selected_ua,
            'proxy': selected_proxy
        }

        async def update_progress():
            stages = ["⬇️ Downloading...\n`[▓▓░░░░░░░░] 25%`", "⬇️ Downloading...\n`[▓▓▓▓▓░░░░░] 55%`", "⬇️ Downloading...\n`[▓▓▓▓▓▓▓▓░░] 85%`", "⚡ Processing File..."]
            for stage in stages:
                await asyncio.sleep(1.2)
                try:
                    await status_msg.edit_text(stage, parse_mode="Markdown")
                except Exception:
                    pass

        progress_task = asyncio.create_task(update_progress())

        def download_file():
            with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                d_info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(d_info)

        filename = await loop.run_in_executor(None, download_file)
        progress_task.cancel()

        await status_msg.edit_text("📤 Telegram-এ সেন্ড করা হচ্ছে...")

        with open(filename, 'rb') as f:
            if mode == 'audio':
                await update.message.reply_audio(audio=f, caption="🎵 Downloaded via Auto Bot")
            else:
                await update.message.reply_video(video=f, caption="🎥 Downloaded via Auto Bot")

        await status_msg.delete()
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await status_msg.edit_text("❌ ডাউনলোড করতে সমস্যা হয়েছে! আবার চেষ্টা করুন।")

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
            
