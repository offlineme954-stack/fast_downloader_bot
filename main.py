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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Android 10; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

# ==================== কীবোর্ড লেআউট ====================
def get_user_keyboard():
    keyboard = [
        [KeyboardButton("💎 𝙏𝙞𝙠𝙏𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙"), KeyboardButton("💎 𝙁𝙖𝙘𝙚𝙗𝙤𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙")],
        [KeyboardButton("💎 𝙔𝙤𝙪𝙏𝙪𝙗𝙚 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙"), KeyboardButton("💎 𝙄𝙣𝙨𝙩𝙖𝙜𝙧𝙖𝙢 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙")],
        [KeyboardButton("🌐 𝙄𝙢𝙖𝙜𝙚 𝙇𝙞𝙣𝙠 𝘾𝙧𝙚𝙖𝙩𝙤𝙧"), KeyboardButton("🔳 𝙌𝙍 𝘾𝙤𝙙𝙚 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧")],
        [KeyboardButton("🎧 𝘼𝙪𝙙𝙞𝙤 𝙊𝙣𝙡𝙮 (𝙈𝙋𝟯)"), KeyboardButton("⚡ 𝙒𝙚𝙗 𝘿𝙞𝙧𝙚𝙘𝙩 𝙇𝙞𝙣𝙠")],
        [KeyboardButton("🗑️ 𝘾𝙡𝙚𝙖𝙧 𝘾𝙝𝙖𝙩 𝙃𝙞𝙨𝙩𝙤𝙧𝙮")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ১০টি ইমেজ হোস্ট এপিআই ====================
def upload_image_multi(file_path):
    apis = [
        lambda f: requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        lambda f: requests.post("https://freeimage.host/api/1/upload", data={"key": "6d207e02198a847aa98d0a2a901485a5"}, files={"source": f}, timeout=10).json().get("image", {}).get("url"),
        lambda f: requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=10).json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/"),
        lambda f: requests.post("https://litterbox.catbox.moe/resources/internals/api.php", data={"reqtype": "fileupload", "time": "1h"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        lambda f: requests.post("https://api.imgbb.com/1/upload?key=6d207e02198a847aa98d0a2a901485a5", files={"image": f}, timeout=10).json().get("data", {}).get("url"),
        lambda f: requests.post("https://file.io", files={"file": f}, timeout=10).json().get("link"),
        lambda f: "https://pixeldrain.com/api/file/" + requests.post("https://pixeldrain.com/api/file", files={"file": f}, timeout=10).json().get("id", ""),
        lambda f: requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        lambda f: requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=10).json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/"),
        lambda f: requests.post("https://freeimage.host/api/1/upload", data={"key": "6d207e02198a847aa98d0a2a901485a5"}, files={"source": f}, timeout=10).json().get("image", {}).get("url")
    ]
    
    for api in apis:
        try:
            with open(file_path, 'rb') as f:
                res = api(f)
                if res and str(res).startswith("http"):
                    return str(res)
        except Exception:
            continue
    return None

# ==================== ৭টি QR কোড এপিআই ====================
def generate_qr_multi_api(text_data):
    encoded = urllib.parse.quote(text_data)
    qr_apis = [
        f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={encoded}",
        f"https://quickchart.io/qr?text={encoded}&size=400",
        f"https://chart.googleapis.com/chart?cht=qr&chs=400x400&chl={encoded}",
        f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={encoded}&color=000000",
        f"https://quickchart.io/qr?text={encoded}&size=500&dark=000000",
        f"https://chart.googleapis.com/chart?cht=qr&chs=500x500&chl={encoded}",
        f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}"
    ]
    for url in qr_apis:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return qr_apis[0]

# ==================== ৫টি অডিও ডাউনলোড এপিআই/ইঞ্জিন ====================
def download_audio_multi_engine(url, file_prefix, user_agent):
    audio_configs = [
        # Method 1: Best quality M4A/MP3 Extractor
        {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
            'user_agent': user_agent
        },
        # Method 2: Direct Audio Stream Exporter
        {
            'format': 'ba/b',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'quiet': True,
            'user_agent': user_agent
        },
        # Method 3: Low-Bitrate Fast Saver
        {
            'format': 'worst[ext=mp3]/worstaudio',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'quiet': True,
            'user_agent': user_agent
        },
        # Method 4: Generic Fallback Audio Extractor
        {
            'format': 'bestaudio',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'quiet': True,
            'nocheckcertificate': True
        },
        # Method 5: Ultra-compatible MP3 Format
        {
            'format': 'bestaudio/best',
            'outtmpl': f'{file_prefix}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            'quiet': True
        }
    ]

    for config in audio_configs:
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Check for mp3 converted name
                base_name = os.path.splitext(filename)[0]
                if os.path.exists(f"{base_name}.mp3"):
                    return f"{base_name}.mp3"
                if os.path.exists(filename):
                    return filename
        except Exception:
            continue
    return None

# ==================== হ্যান্ডলারস ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data['mode'] = 'video'
    
    welcome_msg = (
        "╔═════════════════════════════════╗\n"
        "   ✨ **𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙐𝙇𝙏𝙍𝘼 𝙈𝙐𝙇𝙏𝙄 𝘿𝙊𝙒𝙉𝙇𝙊𝘼𝘿𝙀𝙍** ✨\n"
        "╚═════════════════════════════════╝\n\n"
        "🔥 **হাই-স্পিড অটোমেটেড ইঞ্জিন সাপোর্ট:**\n"
        " ┌─⚡ **২০+ আল্ট্রা সার্ভার:** TikTok, FB, YT, Insta\n"
        " ├─🖼️ **১০টি হাই-স্পিড এপিআই:** Image To Direct Link\n"
        " ├─🔳 **৭টি ব্যাকআপ এপিআই:** QR Code Generator\n"
        " └─🎧 **৫টি অডিও ইঞ্জিন:** High-Quality MP3 Downloader\n\n"
        "💎 *যেকোনো মিডিয়া লিংক বা ছবি পাঠান, বাকিটা স্বয়ংক্রিয়ভাবে প্রসেস হবে!*\n\n"
        "👇 **নিচের প্রফেশনাল মেনু থেকে আপনার সুবিধা নির্বাচন করুন:**"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_user_keyboard())

async def clear_chat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_msg_id = update.message.message_id
    
    status_msg = await update.message.reply_text("🧹 **চ্যাট ব্যাকলগ এবং ইতিহাস মুছে ফেলা হচ্ছে...**", parse_mode="Markdown")
    
    for i in range(current_msg_id, max(1, current_msg_id - 100), -1):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=i)
        except Exception:
            pass
            
    final_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="✨ **চ্যাট অপশন সফলভাবে পরিষ্কার করা হয়েছে!**\nসব পুরাতন মেসেজ রিমুভ করা হয়েছে।",
        reply_markup=get_user_keyboard()
    )
    await asyncio.sleep(4)
    try:
        await final_msg.delete()
    except Exception:
        pass

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    mode = context.user_data.get('mode', 'image')
    
    status_msg = await update.message.reply_text("⚙️ **ছবি বিশ্লেষণ করে সার্ভারে আপলোড করা হচ্ছে...**")
    user_photo_msg_id = update.message.message_id
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        temp_path = f"img_{user_photo_msg_id}.jpg"
        await photo_file.download_to_drive(temp_path)
        
        loop = asyncio.get_event_loop()
        direct_link = await loop.run_in_executor(None, upload_image_multi, temp_path)

        if direct_link:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_photo_msg_id)
                await status_msg.delete()
            except Exception: pass

            if mode == 'qrcode':
                qr_img_url = generate_qr_multi_api(direct_link)
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=qr_img_url,
                    caption=f"🔳 **𝙌𝙍 𝘾𝙤𝙙𝙚 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮!**\n\n🔗 **Direct Image URL:**\n`{direct_link}`",
                    parse_mode="Markdown",
                    reply_markup=get_user_keyboard()
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ **𝙄𝙢𝙖𝙜𝙚 𝘿𝙞𝙧𝙚𝙘𝙩 𝙇𝙞𝙣𝙠 𝘾𝙧𝙚𝙖𝙩𝙤𝙧:**\n\n🔗 `{direct_link}`",
                    parse_mode="Markdown",
                    reply_markup=get_user_keyboard()
                )
        else:
            await status_msg.edit_text("❌ সকল এপিআই সার্ভার ব্যস্ত! অনুগ্রহ করে পুনরায় চেষ্টা করুন।")
    except Exception:
        await status_msg.edit_text("❌ ছবি প্রসেস করতে ত্রুটি ঘটেছে।")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)

    if text in ["💎 𝙏𝙞𝙠𝙏𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙", "💎 𝙁𝙖𝙘𝙚𝙗𝙤𝙤𝙠 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙", "💎 𝙔𝙤𝙪𝙏𝙪𝙗𝙚 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙", "💎 𝙄𝙣𝙨𝙩𝙖𝙜𝙧𝙖𝙢 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙"]:
        context.user_data['mode'] = 'video'
        await update.message.reply_text("🎬 **ভিডিও ডাউনলোড মোড অ্যাক্টিভ।**\nআপনার লিঙ্কটি পাঠান:", reply_markup=get_user_keyboard())
        return
    elif text == "🌐 𝙄𝙢𝙖𝙜𝙚 𝙇𝙞𝙣𝙠 𝘾𝙧𝙚𝙖𝙩𝙤𝙧":
        context.user_data['mode'] = 'image'
        await update.message.reply_text("📸 **ইমেজ লিঙ্ক ক্রিয়েটর মোড অ্যাক্টিভ।**\nযেকোনো ছবি পাঠান:", reply_markup=get_user_keyboard())
        return
    elif text == "🔳 𝙌𝙍 𝘾𝙤𝙙𝙚 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧":
        context.user_data['mode'] = 'qrcode'
        await update.message.reply_text("🔳 **QR কোড জেনারেটর মোড অ্যাক্টিভ।**\nলিঙ্ক বা ছবি পাঠান:", reply_markup=get_user_keyboard())
        return
    elif text == "🎧 𝘼𝙪𝙙𝙞𝙤 𝙊𝙣𝙡𝙮 (𝙈𝙋𝟯)":
        context.user_data['mode'] = 'audio'
        await update.message.reply_text("🎵 **MP3 অডিও মোড অ্যাক্টিভ (৫টি এপিআই ইঞ্জিনের সাথে)।**\nলিঙ্ক পাঠালে অডিও পাঠানো হবে:", reply_markup=get_user_keyboard())
        return
    elif text == "⚡ 𝙒𝙚𝙗 𝘿𝙞𝙧𝙚𝙘𝙩 𝙇𝙞𝙣𝙠":
        context.user_data['mode'] = 'weblink'
        await update.message.reply_text("⚡ **ডাইরেক্ট স্ট্রিম লিঙ্ক মোড অ্যাক্টিভ।**\nলিঙ্ক পাঠালে সরাসরি ডাউনলোডের ডাইরেক্ট লিংক দেওয়া হবে:", reply_markup=get_user_keyboard())
        return
    elif text == "🗑️ 𝘾𝙡𝙚𝙖𝙧 𝘾𝙝𝙖𝙩 𝙃𝙞𝙨𝙩𝙤𝙧𝙮":
        await clear_chat_history(update, context)
        return

    mode = context.user_data.get('mode', 'video')

    if mode == 'qrcode' or (not text.startswith("http") and mode != 'weblink'):
        if mode == 'qrcode':
            qr_img_url = generate_qr_multi_api(text)
            await update.message.reply_photo(photo=qr_img_url, caption=f"🔳 **𝙌𝙍 𝘾𝙤𝙙𝙚 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙!**\n\n`{text}`", parse_mode="Markdown")
            return
        elif not text.startswith("http"):
            await update.message.reply_text("❌ অনুগ্রহ করে সঠিক লিঙ্ক অথবা ছবি পাঠান।", reply_markup=get_user_keyboard())
            return

    url = text
    status_msg = await update.message.reply_text("🔍 **লিঙ্ক এনালাইজ করা হচ্ছে...**")
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
        
        if mode == 'weblink':
            direct_url = info.get('url') or (info['formats'][-1].get('url') if 'formats' in info else None)
            await status_msg.edit_text(f"🔗 **Direct Stream Link:**\n\n`{direct_url}`", parse_mode="Markdown")
            return

        await status_msg.edit_text("⚡ **ফাইল ডাউনলোড হচ্ছে...**")
        file_prefix = f"dl_{update.message.message_id}"

        if mode == 'audio':
            filename = await loop.run_in_executor(None, download_audio_multi_engine, url, file_prefix, selected_ua)
        else:
            ydl_download_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{file_prefix}.%(ext)s',
                'quiet': True,
                'user_agent': selected_ua,
                'nocheckcertificate': True
            }
            def download_file():
                with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                    d_info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(d_info)
            filename = await loop.run_in_executor(None, download_file)

        if not filename or not os.path.exists(filename):
            await status_msg.edit_text("❌ অডিও/ভিডিও ফাইলটি প্রসেস করা সম্ভব হয়নি।")
            return

        file_size = os.path.getsize(filename) / (1024 * 1024)
        if file_size > 49:
            direct_url = info.get('url') or (info['formats'][-1].get('url') if 'formats' in info else None)
            await status_msg.edit_text(
                f"⚠️ **ফাইল সাইজ ৫০ MB-র বেশি ({file_size:.1f} MB)!**\n\n"
                f"টেলিগ্রাম লিমিটের কারণে সরাসরি সেন্ড সম্ভব নয়। নিচে ডাইরেক্ট লিংক দেওয়া হলো:\n\n"
                f"📥 **Fast Direct Download Link:**\n`{direct_url}`",
                parse_mode="Markdown"
            )
            return

        await status_msg.edit_text("📤 **টেলিগ্রামে আপলোড করা হচ্ছে...**")

        try:
            with open(filename, 'rb') as f:
                if mode == 'audio':
                    await asyncio.wait_for(update.message.reply_audio(audio=f, caption="🎧 **Downloaded via Ultra Downloader Bot**"), timeout=60)
                else:
                    await asyncio.wait_for(update.message.reply_video(video=f, caption="🎥 **Downloaded via Ultra Downloader Bot**"), timeout=90)
            await status_msg.delete()
        except asyncio.TimeoutError:
            direct_url = info.get('url') or (info['formats'][-1].get('url') if 'formats' in info else None)
            await status_msg.edit_text(f"⚠️ **নেটওয়ার্ক স্লো হওয়ায় ফাইলটি সেন্ড করা যায়নি!**\n\n📥 **Direct Link:**\n`{direct_url}`", parse_mode="Markdown")

    except Exception:
        await status_msg.edit_text("❌ লিঙ্কটি প্রসেস করা সম্ভব হয়নি! লিংকটি সঠিক রয়েছে কিনা নিশ্চিত করুন।")
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception: pass

# ==================== মূল প্রোগ্রাম ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_chat_history))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot with 5 Audio Engines Updated and Running!")
    app.run_polling()

if __name__ == "__main__":
    main()
        
