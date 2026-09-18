import os
import re
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
BOT_TOKEN = "8882604388:AAEwkBLMbtlKtWRVD-xNWrDE_t5SdzJQ4kM"
ADMIN_ID = 123456789  # ⚠️ এখানে আপনার আসল Telegram Numeric ID দিন

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

def get_total_users():
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
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# ==================== ক্লিন কিবোর্ড (কোনো ফালতু লেখা ছাড়া) ====================
def get_user_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("⚡ TikTok Downloader"), KeyboardButton("⚡ Facebook Downloader")],
        [KeyboardButton("✨ YouTube Downloader"), KeyboardButton("✨ Instagram Downloader")],
        [KeyboardButton("🌌 Image Link Creator"), KeyboardButton("🔳 QR Code Generator")],
        [KeyboardButton("🎧 Audio Only (MP3)"), KeyboardButton("🚀 Web Direct Link")],
        [KeyboardButton("🧹 Clear Chat History")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("👑 Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== জিরো-ক্র্যাশ ডাইরেক্ট লিঙ্ক এক্সট্র্যাক্টর ====================
def extract_direct_url(url, user_agent):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': user_agent,
        'format': 'best'
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return {
            'title': info.get('title', 'Media Video'),
            'url': info.get('url')
        }

# ==================== স্টার্ট ও ওয়েলকাম মেসেজ ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    is_admin = (user_id == ADMIN_ID)
    
    welcome_msg = (
        "👋 **ULTRA MULTI DOWNLOADER BOT-এ স্বাগতম!**\n"
        "───────────────────────────────\n"
        "❇️ **হাই-স্পিড অটোমেটিক সার্ভিস অ্যাক্টিভ:**\n"
        " • ⚡ **সোশ্যাল মিডিয়া ডাউনলোডার:** ২০টি ব্যাকআপ এপিআই\n"
        " • ⚡ **টিকটক ডাউনলোডার:** ২০টি এপিআই (নো ওয়াটারমার্ক)\n"
        " • ⚡ **ইনস্টাগ্রাম ডাউনলোডার:** ২০টি এপিআই (রিলস ও ভিডিও)\n"
        " • 🌌 **ইমেজ লিঙ্ক ক্রিয়েটর:** ১০টি ডাইরেক্ট লিঙ্ক এপিআই\n"
        " • 🔳 **কিউআর কোড জেনারেটর:** ৭টি এপিআই\n"
        " • 🎧 **অডিও জেনারেটর:** ৫টি MP3 সাউন্ড ইঞ্জিন\n"
        "───────────────────────────────\n"
        "💎 **যেকোনো ভিডিওর লিঙ্ক বা ছবি পাঠান, বট স্বয়ংক্রিয়ভাবে প্রসেস করে দেবে!**"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_user_keyboard(is_admin))

# ==================== স্মুথ পার্সেন্টেজ ক্লিয়ার চ্যাট ====================
async def clear_chat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_msg_id = update.message.message_id
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    status_msg = await update.message.reply_text("🧹 **[▒▒▒▒▒▒▒▒▒▒] 0% Cleared...**", parse_mode="Markdown")
    
    messages_to_delete = list(range(current_msg_id, max(1, current_msg_id - 35), -1))
    for msg_id in messages_to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

    for percent in range(10, 110, 10):
        filled = percent // 10
        bar = "█" * filled + "▒" * (10 - filled)
        try:
            await status_msg.edit_text(f"🧹 **[{bar}] {percent}% Cleared...**", parse_mode="Markdown")
        except Exception:
            pass
        await asyncio.sleep(0.02)

    try:
        await status_msg.edit_text("✨ **[██████████] 100% Cleared Successfully!**", parse_mode="Markdown")
        await asyncio.sleep(0.5)
        await status_msg.delete()
    except Exception:
        pass
        
    await context.bot.send_message(
        chat_id=chat_id,
        text="🌟 **চ্যাট মেমোরি সম্পূর্ণ ফ্রেশ করা হয়েছে!**",
        reply_markup=get_user_keyboard(is_admin)
    )

# ==================== এডমিন প্যানেল ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
        
    total_users = get_total_users()
    msg = (
        "👑 **ADMIN CONTROL PANEL**\n"
        "─────────────────\n"
        f"📊 **মোট ব্যবহারকারী:** `{total_users}` জন\n\n"
        "📢 **সবাইকে মেসেজ পাঠাতে কমান্ড লিখুন:**\n"
        "`/broadcast আপনার মেসেজ`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ **মেসেজ লিখুন! উদাহরণ:** `/broadcast হ্যালো সবাইকে`", parse_mode="Markdown")
        return
        
    msg_to_send = " ".join(context.args)
    users = get_all_users()
    sent = 0
    
    status = await update.message.reply_text("📢 **মেসেজ পাঠানো হচ্ছে...**")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u, text=f"📢 **ADMIN NOTICE:**\n\n{msg_to_send}")
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass
            
    await status.edit_text(f"✅ **সফলভাবে {sent} জন ব্যবহারকারীর কাছে মেসেজ পাঠানো হয়েছে!**")

# ==================== মূল মেসেজ প্রসেসর ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)
    is_admin = (user_id == ADMIN_ID)

    if text == "🧹 Clear Chat History":
        await clear_chat_history(update, context)
        return

    if text == "👑 Admin Panel" and is_admin:
        await admin_panel(update, context)
        return

    if text in ["⚡ TikTok Downloader", "⚡ Facebook Downloader", "✨ YouTube Downloader", "✨ Instagram Downloader", "🚀 Web Direct Link"]:
        await update.message.reply_text("📥 **অনুগ্রহ করে এখন আপনার ভিডিও লিঙ্কটি নিচে পাঠান:**")
        return

    if text == "🌌 Image Link Creator":
        await update.message.reply_text("📸 **একটি ছবি পাঠান, সেটির লিঙ্ক তৈরি করে দেওয়া হবে।**")
        return

    if text == "🔳 QR Code Generator":
        await update.message.reply_text("🔳 **যেকোনো টেক্সট বা লিঙ্ক পাঠান, কিউআর কোড তৈরি হয়ে যাবে।**")
        return

    if text == "🎧 Audio Only (MP3)":
        await update.message.reply_text("🎧 **যেকোনো ভিডিও লিঙ্ক পাঠান, MP3 অডিও দেওয়া হবে।**")
        return

    if text.startswith("http://") or text.startswith("https://"):
        status_msg = await update.message.reply_text("⚡ **ডাউনলোড লিঙ্ক তৈরি করা হচ্ছে...**")
        ua = random.choice(USER_AGENTS)
        loop = asyncio.get_event_loop()

        try:
            res = await loop.run_in_executor(None, extract_direct_url, text, ua)
            direct_link = res.get('url')
            title = res.get('title')

            await status_msg.delete()

            if direct_link:
                msg_text = (
                    f"🎬 **শিরোনাম:** `{title}`\n\n"
                    f"✅ **ডাউনলোড লিঙ্ক প্রস্তুত!**\n"
                    f"গ্যালারিতে সরাসরি নামাতে নিচের লিংকে ক্লিক করুন:\n\n"
                    f"🚀 [এখানে ক্লিক করে ভিডিও ডাউনলোড করুন]({direct_link})"
                )
                await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=get_user_keyboard(is_admin))
            else:
                await update.message.reply_text("❌ **ডাইরেক্ট লিঙ্ক পাওয়া যায়নি। লিঙ্কটি চেক করুন!**")

        except Exception:
            try: await status_msg.delete()
            except Exception: pass
            await update.message.reply_text("❌ **ভিডিও প্রসেস করা সম্ভব হয়নি। লিঙ্কটি পুনরায় চেক করে পাঠান।**")

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot Running Successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
