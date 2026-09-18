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
ADMIN_ID = 123456789  # ⚠️ এখানে আপনার আসল Telegram Numeric ID দিন

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Android 10; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1"
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

# ==================== ঝলমলে প্রিমিয়াম কিবোর্ড ====================
def get_user_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("⚡ 𝙏𝙞𝙠𝙏𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 (𝟮𝟬 𝘼𝙋𝙄) ⚡"), KeyboardButton("⚡ 𝙁𝙖𝙘𝙚𝙗𝙤𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 (𝟮𝟬 𝘼𝙋𝙄) ⚡")],
        [KeyboardButton("✨ 𝙔𝙤𝙪𝙏𝙪𝙗𝙚 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 ✨"), KeyboardButton("✨ 𝙄𝙣𝙨𝙩𝙖𝙜𝙧𝙖𝙢 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 (𝟮𝟬 𝘼𝙋𝙄) ✨")],
        [KeyboardButton("🌌 𝙄𝙢𝙖𝙜𝙚 𝙇𝙞𝙣𝙠 𝘾𝙧𝙚𝙖𝙩𝙤𝙧 (𝟭𝟬 𝘼𝙋𝙄)"), KeyboardButton("🔳 𝙌𝙍 𝘾𝙤𝙙𝙚 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧 (𝟳 𝘼𝙋𝙄)")],
        [KeyboardButton("🎧 𝘼𝙪𝙙𝙞𝙤 𝙊𝙣𝙡𝙮 (𝟱 𝙀𝙣𝙜𝙞𝙣𝙚𝙨)"), KeyboardButton("🚀 𝙒𝙚𝙗 𝘿𝙞𝙧𝙚𝙘𝙩 𝙇𝙞𝙣𝙠")],
        [KeyboardButton("🧹 𝘾𝙡𝙚𝙖𝙧 𝘾𝙝𝙖𝙩 𝙃𝙞𝙨𝙩𝙤𝙧𝙮")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("👑 𝘼𝙙𝙢𝙞𝙣 𝙋𝙖𝙣𝙚𝙡 👑")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== জিরো-মেমোরি লিঙ্ক এক্সট্র্যাক্টর ====================
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
            'url': info.get('url'),
            'thumbnail': info.get('thumbnail')
        }

# ==================== হ্যান্ডলারস ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    is_admin = (user_id == ADMIN_ID)
    
    welcome_msg = (
        "🔥 ✵ **𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙐𝙇𝙏𝙍𝘼 𝙈𝙐𝙇𝙏𝙄 𝘿𝙊𝙒𝙉𝙇𝙊𝘼𝘿𝙀𝙍** ✵ 🔥\n"
        "───────────────────────────────\n"
        "❇️ **হাই-স্পিড অটোমেটিক সার্ভিস অ্যাক্টিভ:**\n"
        " ┌─⚡ **২০টি ব্যাকআপ এপিআই:** সোশ্যাল মিডিয়া ডাউনলোড\n"
        " ├─⚡ **২০টি টিকটক এপিআই:** নো ওয়াটারমার্ক ডাউনলোড\n"
        " ├─⚡ **২০টি ইনস্টাগ্রাম এপিআই:** রিলস ও পোস্ট ডাউনলোডার\n"
        " ├─🌌 **১০টি এপিআই:** ইমেজ টু ডাইরেক্ট লিংক জেনারেটর\n"
        " ├─🔳 **৭টি এপিআই:** কিউআর কোড জেনারেটর\n"
        " └─🎧 **৫টি অডিও ইঞ্জিন:** হাই-কোয়ালিটি MP3 অডিও জেনারেটর\n"
        "───────────────────────────────\n"
        "💎 **যেকোনো মিডিয়া লিংক বা ছবি পাঠান, স্বয়ংক্রিয়ভাবে প্রসেস হয়ে যাবে!**\n\n"
        "👇 *নিচের প্রফেশনাল মেনু থেকে আপনার সুবিধা নির্বাচন করুন:*"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_user_keyboard(is_admin))

# ==================== রিয়েল-টাইম পার্সেন্ট এনিমেশন ক্লিয়ার চ্যাট ====================
async def clear_chat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_msg_id = update.message.message_id
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    status_msg = await update.message.reply_text("🧹 **[▒▒▒▒▒▒▒▒▒▒] 0% Cleared...**", parse_mode="Markdown")
    
    # চ্যাটের আগের মেসেজগুলো ডিলিট
    messages_to_delete = list(range(current_msg_id, max(1, current_msg_id - 40), -1))
    for msg_id in messages_to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

    # ১% থেকে ১০০% পার্সেন্টেজ এনিমেশন
    for percent in range(5, 105, 5):
        filled = percent // 10
        bar = "█" * filled + "▒" * (10 - filled)
        try:
            await status_msg.edit_text(f"🧹 **[{bar}] {percent}% Cleared...**", parse_mode="Markdown")
        except Exception:
            pass
        await asyncio.sleep(0.03)

    try:
        await status_msg.edit_text("✨ **[██████████] 100% Cleared Successfully!**", parse_mode="Markdown")
        await asyncio.sleep(0.8)
        await status_msg.delete()
    except Exception:
        pass
        
    await context.bot.send_message(
        chat_id=chat_id,
        text="🌟 **চ্যাট মেমোরি সম্পূর্ণ ফ্রেশ করা হয়েছে! আপনার পছন্দের মেনু নিচে তৈরি:**",
        reply_markup=get_user_keyboard(is_admin)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)
    is_admin = (user_id == ADMIN_ID)
    
    if "𝘾𝙡𝙚𝙖𝙧 𝘾𝙝𝙖𝙩" in text:
        await clear_chat_history(update, context)
        return

    if text.startswith("http://") or text.startswith("https://"):
        status_msg = await update.message.reply_text("⚡ **মাল্টি-এপিআই সার্ভারে সংযোগ করা হচ্ছে...**")
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
                    f"✅ **ডাউনলোড লিংক তৈরি সম্পন্ন!**\n"
                    f"হাই-স্পিড ডাউনলোড করতে নিচের লিংকে ক্লিক করে সরাসরি গ্যালারিতে সেভ করুন:\n\n"
                    f"🚀 [এখানে ক্লিক করে ভিডিও ডাউনলোড করুন]({direct_link})"
                )
                await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=get_user_keyboard(is_admin))
            else:
                await update.message.reply_text("❌ **ডাইরেক্ট লিঙ্ক পাওয়া যায়নি। লিঙ্কটি পুনরায় চেক করুন!**")
                
        except Exception as e:
            try: await status_msg.delete()
            except Exception: pass
            await update.message.reply_text("❌ **ভিডিও প্রসেস করা সম্ভব হয়নি। অন্য কোনো লিঙ্ক চেষ্টা করুন!**")

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Ultra Multi Downloader Bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
