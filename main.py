import os
import re
import math
import random
import asyncio
import logging
import sqlite3
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
BOT_TOKEN = "8882604388:AAEdojjIT4emGLkX3HesBKvDx4dUEpgJLaA"
ADMIN_ID = 7454712269

# ১০-২০টি পাবলিক হাই-অ্যানোনিমিটি প্রক্সি তালিকা (ফেল-সেফ সাপোর্ট)
FREE_PROXIES = [
    "http://185.199.229.156:7492",
    "http://185.199.228.220:7300",
    "http://185.199.231.45:8382",
    "http://188.166.205.155:3128",
    "http://159.65.133.175:3128",
    "http://165.225.208.84:80",
    "http://165.225.222.241:80",
    "http://138.68.60.8:8080",
    "http://51.159.66.10:80",
    "http://51.158.123.35:8888",
    "http://163.172.31.28:8888",
    "http://51.15.242.200:8888",
    "http://51.158.106.54:8888",
    "http://163.172.48.117:8888",
    "http://51.15.166.107:8888"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== ডাটাবেজ ফাংশন ====================
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

# ==================== প্রধান কীবোর্ড ====================
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎬 TikTok Download"), KeyboardButton("📘 Facebook Download")],
        [KeyboardButton("🔴 YouTube Download"), KeyboardButton("📸 Instagram Download")],
        [KeyboardButton("🎵 Audio Only (MP3)"), KeyboardButton("🔗 Web Direct Link")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== কমান্ড হ্যান্ডলার ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    context.user_data['mode'] = 'video'
    
    text = (
        "👋 **স্বাগতম!**\n\n"
        "যেকোনো TikTok, Facebook, YouTube বা Instagram ভিডিওর লিংক পাঠান।\n"
        "⚡ *সর্বোচ্চ ১০ মিনিটের ভিডিও ডাউনলোড করা যাবে।*\n\n"
        "নিচের বাটনগুলো দিয়ে আপনার পছন্দের অপশন সিলেক্ট করুন:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ==================== মেসেজ ও ডাউনলোড প্রসেস ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)

    # মোড চেঞ্জ ফিল্টার
    if text == "🎬 TikTok Download":
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ TikTok ভিডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক দিন:", reply_markup=get_main_keyboard())
        return
    elif text == "📘 Facebook Download":
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ Facebook ভিডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক দিন:", reply_markup=get_main_keyboard())
        return
    elif text == "🔴 YouTube Download":
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ YouTube ভিডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক দিন:", reply_markup=get_main_keyboard())
        return
    elif text == "📸 Instagram Download":
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ Instagram ভিডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক দিন:", reply_markup=get_main_keyboard())
        return
    elif text == "🎵 Audio Only (MP3)":
        context.user_data['mode'] = 'audio'
        await update.message.reply_text("🎵 MP3 অডিও ডাউনলোড মোড সিলেক্ট করা হয়েছে। এখন লিংক দিন:", reply_markup=get_main_keyboard())
        return
    elif text == "🔗 Web Direct Link":
        context.user_data['mode'] = 'weblink'
        await update.message.reply_text("🔗 Web Link জেনারেট মোড সিলেক্ট করা হয়েছে। লিংক দিন:", reply_markup=get_main_keyboard())
        return

    # URL চেক
    url_pattern = re.compile(r'https?://[^\s]+')
    if not url_pattern.match(text):
        await update.message.reply_text("❌ অনুগ্রহ করে সঠিক ভিডিও লিংক পাঠান।", reply_markup=get_main_keyboard())
        return

    url = text
    mode = context.user_data.get('mode', 'video')

    status_msg = await update.message.reply_text("🔍 ভিডিও ইনফরমেশন চেক করা হচ্ছে...")

    # yt-dlp অপশন কনফিগারেশন
    selected_proxy = random.choice(FREE_PROXIES)
    selected_ua = random.choice(USER_AGENTS)

    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': selected_ua,
        'proxy': selected_proxy
    }

    try:
        loop = asyncio.get_event_loop()
        
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, fetch_info)
        duration = info.get('duration', 0)

        # ১০ মিনিটের বেশি হলে বাতিল (৬০০ সেকেন্ড)
        if duration and duration > 600:
            await status_msg.edit_text("❌ ভিডিওটি ১০ মিনিটের বেশি বড়! ১০ মিনিটের কম দৈর্ঘ্যের ভিডিও লিংক দিন।")
            return

        # ওয়েবসাইট ব্যবহারে ডাইরেক্ট লিংক এক্সট্র্যাক্ট
        if mode == 'weblink':
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                direct_url = info['formats'][-1].get('url')

            if direct_url:
                res_text = (
                    "🔗 **Web Direct Stream Link (For Website):**\n\n"
                    f"`{direct_url}`\n\n"
                    "💡 এই লিংকটি আপনার ওয়েবসাইটের `<video>` বা `<audio>` ট্যাগে সরাসরি ব্যবহার করতে পারবেন।"
                )
                await status_msg.edit_text(res_text, parse_mode="Markdown")
            else:
                await status_msg.edit_text("❌ ডাইরেক্ট ওয়েব লিংক জেনারেট করা সম্ভব হয়নি।")
            return

        # ফাইল ডাউনলোড মোড
        await status_msg.edit_text("⬇️ Downloading...\n`[░░░░░░░░░░] 0%`", parse_mode="Markdown")

        file_prefix = f"dl_{update.message.message_id}"
        
        if mode == 'audio':
            ydl_download_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{file_prefix}.%(ext)s',
                'quiet': True,
                'user_agent': selected_ua,
                'proxy': selected_proxy
            }
        else:
            ydl_download_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{file_prefix}.mp4',
                'quiet': True,
                'user_agent': selected_ua,
                'proxy': selected_proxy
            }

        # অ্যানিমেশন আপডেট
        async def update_progress():
            stages = [
                "⬇️ Downloading...\n`[▓▓░░░░░░░░] 25%`",
                "⬇️ Downloading...\n`[▓▓▓▓▓░░░░░] 55%`",
                "⬇️ Downloading...\n`[▓▓▓▓▓▓▓▓░░] 85%`",
                "⚡ Processing Video File..."
            ]
            for stage in stages:
                await asyncio.sleep(1.5)
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

        # ফাইল সেন্ড
        with open(filename, 'rb') as f:
            if mode == 'audio':
                await update.message.reply_audio(audio=f, caption="🎵 Downloaded via Auto Bot")
            else:
                await update.message.reply_video(video=f, caption="🎥 Downloaded via Auto Bot")

        await status_msg.delete()

        # সার্ভার ক্লিনআপ
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await status_msg.edit_text(f"❌ ডাউনলোড করতে সমস্যা হয়েছে! আবার চেষ্টা করুন।\nঅ্যারর: {str(e)[:50]}")

# ==================== এডমিন কমান্ড ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    total_users = get_users_count()
    admin_text = (
        "👑 **Admin Panel**\n\n"
        f"📊 **Total Users:** {total_users}\n\n"
        "📢 **Broadcast করার নিয়ম:**\n"
        "`/broadcast আপনার নোটিশের কথাগুলো`"
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ মেসেজ লিখুন! উদাহরণ:\n`/broadcast আপনার নতুন নোটিশ`", parse_mode="Markdown")
        return

    broadcast_text = " ".join(context.args)
    users = get_all_users()
    success = 0

    status = await update.message.reply_text("📢 ব্রডকাস্ট পাঠানো শুরু হয়েছে...")

    for u_id in users:
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 **Notice:**\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status.edit_text(f"✅ ব্রডকাস্ট সম্পন্ন!\nমোট {success}/{len(users)} জন ইউজার মেসেজ পেয়েছে।")

# ==================== মেইন রানার ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
      
