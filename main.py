import os
import re
import random
import asyncio
import logging
import sqlite3
import urllib.parse
import requests
import yt_dlp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8882604388:AAEwkBLMbtlKtWRVD-xNWrDE_t5SdzJQ4kM"
ADMIN_ID = 7454712269
ADMIN_USERNAME = "Md_atiqul_islam0"

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

# ==================== ডায়নামিক কীবোর্ড ====================
def get_user_keyboard(user_id):
    keyboard = [
        [KeyboardButton("🎬 TikTok Download"), KeyboardButton("📘 Facebook Download")],
        [KeyboardButton("🔴 YouTube Download"), KeyboardButton("📸 Instagram Download")],
        [KeyboardButton("🖼️ Image Link Creator"), KeyboardButton("🔳 QR Code Generator")],
        [KeyboardButton("🎵 Audio Only (MP3)"), KeyboardButton("🔗 Web Direct Link")]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("👑 Admin Panel"), KeyboardButton("👨‍💻 Support / Help")])
    else:
        keyboard.append([KeyboardButton("👨‍💻 Support / Help")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ১০টি ছবি হোস্ট এপিআই ====================
def upload_image_multi(file_path):
    apis = [
        # API 1: Catbox
        lambda f: requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        # API 2: FreeImageHost
        lambda f: requests.post("https://freeimage.host/api/1/upload", data={"key": "6d207e02198a847aa98d0a2a901485a5"}, files={"source": f}, timeout=10).json().get("image", {}).get("url"),
        # API 3: TmpFiles
        lambda f: requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=10).json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/"),
        # API 4: Litterbox
        lambda f: requests.post("https://litterbox.catbox.moe/resources/internals/api.php", data={"reqtype": "fileupload", "time": "1h"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        # API 5: ImgBB
        lambda f: requests.post("https://api.imgbb.com/1/upload?key=6d207e02198a847aa98d0a2a901485a5", files={"image": f}, timeout=10).json().get("data", {}).get("url"),
        # API 6: File.io
        lambda f: requests.post("https://file.io", files={"file": f}, timeout=10).json().get("link"),
        # API 7: Pixeldrain
        lambda f: "https://pixeldrain.com/api/file/" + requests.post("https://pixeldrain.com/api/file", files={"file": f}, timeout=10).json().get("id", ""),
        # API 8: Quackhost
        lambda f: requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=10).text.strip(),
        # API 9: Envfile
        lambda f: requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=10).json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/"),
        # API 10: ImageKit Multi
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

# ==================== হ্যান্ডলারস ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data['mode'] = 'video'
    
    welcome_msg = (
        "🚀 **আমাদের আল্ট্রা-পাওয়ারফুল অল-ইন-ওয়ান ডাউনলোডার বটে আপনাকে স্বাগতম!** 🚀\n\n"
        "⚡ **বটের শক্তিশালী হাইলাইটসমূহ:**\n"
        "• 🎬 **২০+ সার্ভার/এপিআই মেথড** দ্বারা TikTok, FB, YT, Insta ফাস্ট ডাউনলোড\n"
        "• 🖼️ **১০টি ব্যাকআপ এপিআই** বিশিষ্ট Image To Direct Link জেনারেটর\n"
        "• 🔳 **৭টি এপিআই** বিশিষ্ট QR Code Generator (টেক্সট, লিংক ও ছবি সাপোর্টেড)\n"
        "• 🎵 **MP3 Audio Downloader & Direct Web Link**\n\n"
        "✨ *ছবি পাঠালে মূল ছবি মুছে সাথে সাথে লিংক ও QR বানিয়ে দেওয়া হবে!*\n\n"
        "👇 *নিচের মেনু থেকে আপনার সার্ভিস সিলেক্ট করুন:*"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_user_keyboard(user_id))

# ফটো হ্যান্ডলার (ইমেজ লিংক ও ছবি দিয়ে অটো QR জেনারেটর)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    mode = context.user_data.get('mode', 'image')
    
    status_msg = await update.message.reply_text("⏳ ছবি প্রসেস করে ডাইরেক্ট লিংক তৈরি করা হচ্ছে...")
    user_photo_msg_id = update.message.message_id
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        temp_path = f"img_{user_photo_msg_id}.jpg"
        await photo_file.download_to_drive(temp_path)
        
        loop = asyncio.get_event_loop()
        direct_link = await loop.run_in_executor(None, upload_image_multi, temp_path)

        if direct_link:
            # অরিজিনাল ছবি ও স্ট্যাটাস মেসেজ রিমুভ
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_photo_msg_id)
                await status_msg.delete()
            except Exception: pass

            if mode == 'qrcode':
                # ছবি থেকে লিংক বানিয়ে অটো QR কোড তৈরি
                qr_img_url = generate_qr_multi_api(direct_link)
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=qr_img_url,
                    caption=f"🔳 **Image QR Code Generated!**\n\n🔗 **Direct Link:** `{direct_link}`",
                    parse_mode="Markdown",
                    reply_markup=get_user_keyboard(user_id)
                )
            else:
                # শুধু ডাইরেক্ট লিংক সেন্ড
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ **Image Direct Link Created!**\n\n`{direct_link}`",
                    parse_mode="Markdown",
                    reply_markup=get_user_keyboard(user_id)
                )
        else:
            await status_msg.edit_text("❌ সবকটি সার্ভার ব্যস্ত! আবার চেষ্টা করুন।")
    except Exception as e:
        await status_msg.edit_text("❌ ছবি প্রসেস করতে ব্যর্থ হয়েছে।")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    add_user(user_id)

    if text in ["🎬 TikTok Download", "📘 Facebook Download", "🔴 YouTube Download", "📸 Instagram Download"]:
        context.user_data['mode'] = 'video'
        await update.message.reply_text("✅ ভিডিও ডাউনলোড মোড চালু হয়েছে। এখন লিংক পাঠান:", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "🖼️ Image Link Creator":
        context.user_data['mode'] = 'image'
        await update.message.reply_text("📸 যেকোনো ফটো পাঠান, বট লিংক তৈরি করে অরিজিনাল ছবি মুছে দেবে।", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "🔳 QR Code Generator":
        context.user_data['mode'] = 'qrcode'
        await update.message.reply_text("🔳 যেকোনো লিংক, টেক্সট বা ফটো পাঠান, বট QR কোড বানিয়ে দেবে।", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "🎵 Audio Only (MP3)":
        context.user_data['mode'] = 'audio'
        await update.message.reply_text("🎵 MP3 অডিও মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "🔗 Web Direct Link":
        context.user_data['mode'] = 'weblink'
        await update.message.reply_text("🔗 Web Direct Link মোড চালু হয়েছে। ভিডিও লিংক পাঠান:", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "👨‍💻 Support / Help":
        support_msg = (
            "👨‍💻 **Admin & Developer Support**\n\n"
            f"👤 **Admin User:** @{ADMIN_USERNAME}\n"
            f"💬 **Direct Chat:** https://t.me/{ADMIN_USERNAME}"
        )
        await update.message.reply_text(support_msg, parse_mode="Markdown", reply_markup=get_user_keyboard(user_id))
        return
    elif text == "👑 Admin Panel" and user_id == ADMIN_ID:
        await admin_panel_show(update)
        return

    mode = context.user_data.get('mode', 'video')

    if mode == 'qrcode' or (not text.startswith("http") and mode != 'weblink'):
        if mode == 'qrcode':
            qr_img_url = generate_qr_multi_api(text)
            await update.message.reply_photo(photo=qr_img_url, caption=f"🔳 **QR Code Generated!**\n\n`{text}`", parse_mode="Markdown")
            return
        elif not text.startswith("http"):
            await update.message.reply_text("❌ অনুগ্রহ করে সঠিক লিংক বা ছবি পাঠান।", reply_markup=get_user_keyboard(user_id))
            return

    url = text
    status_msg = await update.message.reply_text("🔍 লিঙ্ক এনালাইজ করা হচ্ছে...")
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

        await status_msg.edit_text("⚡ পাওয়ারফুল এপিআই দিয়ে ফাইল ডাউনলোড করা হচ্ছে...")
        file_prefix = f"dl_{update.message.message_id}"
        
        ydl_download_opts = {
            'format': 'best[ext=mp4]/best' if mode == 'video' else 'bestaudio/best',
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

        # ৫০ MB সেফটি ফিল্টার
        file_size = os.path.getsize(filename) / (1024 * 1024)
        if file_size > 49:
            direct_url = info.get('url') or (info['formats'][-1].get('url') if 'formats' in info else None)
            await status_msg.edit_text(
                f"⚠️ **ভিডিওটির সাইজ ৫০ MB-র বেশি ({file_size:.1f} MB)!**\n\n"
                f"টেলিগ্রাম লিমিটের কারণে সরাসরি ভিডিও ফাইল পাঠানো সম্ভব নয়। তবে আপনি নিচের ডাইরেক্ট লিংক থেকে ডাউনলোড করতে পারবেন:\n\n"
                f"📥 **Direct Fast Download Link:**\n`{direct_url}`",
                parse_mode="Markdown"
            )
            return

        await status_msg.edit_text("📤 Telegram-এ সেন্ড করা হচ্ছে...")

        with open(filename, 'rb') as f:
            if mode == 'audio':
                await update.message.reply_audio(audio=f, caption="🎵 Downloaded via All Atikul Downloader Bot")
            else:
                await update.message.reply_video(video=f, caption="🎥 Downloaded via All Atikul Downloader Bot")

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ লিঙ্কটি প্রসেস করা সম্ভব হয়নি! প্রাইভেট বা রেস্ট্রিক্টেড ভিডিও হতে পারে।")
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception: pass

# ==================== এডমিন প্যানেল ====================
async def admin_panel_show(update: Update):
    total_users = get_users_count()
    keyboard = [
        [InlineKeyboardButton("📢 Send Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Total Users", callback_data="admin_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_text = f"👑 **Admin Control Panel**\n\n📊 **Total Bot Users:** `{total_users}`"
    await update.message.reply_text(admin_text, parse_mode="Markdown", reply_markup=reply_markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "admin_stats":
        total_users = get_users_count()
        await query.edit_message_text(f"📊 **Total Active Users:** `{total_users}`", parse_mode="Markdown")
    elif query.data == "admin_broadcast":
        await query.edit_message_text("📢 ব্রডকাস্ট পাঠাতে এই কমান্ডটি চ্যাটে লিখুন:\n\n`/broadcast আপনার নোটিশ বার্তা`", parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ ব্রডকাস্ট পাঠাতে লিখুন:\n`/broadcast আপনার তথ্য`", parse_mode="Markdown")
        return

    broadcast_text = " ".join(context.args)
    users = get_all_users()
    success = 0

    status = await update.message.reply_text("📢 ব্রডকাস্ট মেসেজ পাঠানো শুরু হয়েছে...")

    for u_id in users:
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 **Notification:**\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status.edit_text(f"✅ ব্রডকাস্ট মেসেজ পাঠানো শেষ!\nমোট {success}/{len(users)} জন ইউজার পেয়েছে।")

# ==================== মূল প্রোগ্রাম ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot completely updated & running with Multi-APIs!")
    app.run_polling()

if __name__ == "__main__":
    main()
