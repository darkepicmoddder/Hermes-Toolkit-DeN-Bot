import os
import sys
import shutil
import subprocess
import zipfile
import time
import logging
import threading
import urllib.parse
from datetime import datetime
from telebot import TeleBot, types
from pymongo import MongoClient

# --- CONFIGURATION ---
TOKEN = "8560230565:AAG3NQreOHOmOrOCfJWulf5g6LrlWZo2KPg"
ADMIN_ID = 7498487211
CHANNEL_USERNAME = "@Dark_Epic_Modder"
CHANNEL_URL = "https://t.me/Dark_Epic_Modder"
WHL_FILE = "hbctool-0.1.5-96-py3-none-any.whl"
IMG_URL = "https://raw.githubusercontent.com/darkepicmoddder/Drive-DeM/refs/heads/main/Img/toolkit.jpg"

# --- MONGODB CONNECTION ---
raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
client = MongoClient(raw_uri)
db = client['hermes_ultra_db']
users_col = db['users']

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=30)
logging.basicConfig(level=logging.INFO)

# --- UI HELPERS ---
def get_progress_bar(percent):
    done = int(percent / 10)
    bar = "█" * done + "░" * (10 - done)
    return f"[{bar}] {percent}%"

def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📂 My Profile", callback_data="my_profile"),
        types.InlineKeyboardButton("📜 Commands", callback_data="help_cmd"),
        types.InlineKeyboardButton("📢 Channel", url=CHANNEL_URL),
        types.InlineKeyboardButton("👤 Developer", url="https://t.me/DarkEpicModderBD0x1")
    )
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"))
    return markup

# --- DATABASE ---
def sync_user(user):
    u = users_col.find_one({"user_id": user.id})
    if not u:
        users_col.insert_one({
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "N/A",
            "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "total_tasks": 0
        })
    return u

def check_join(user_id):
    if user_id == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- ENGINE ---
def bootstrap_engine():
    try:
        if os.path.exists(WHL_FILE):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", WHL_FILE])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "hbctool"])
        import hbctool.hbc
        if 96 not in hbctool.hbc.HBC:
            v = max(hbctool.hbc.HBC.keys())
            hbctool.hbc.HBC[96] = hbctool.hbc.HBC[v]
    except: pass

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    sync_user(message.from_user)
    if not check_join(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        return bot.send_photo(message.chat.id, IMG_URL, caption="<b>⚠️ ACCESS DENIED!</b>\nPlease join our channel to use the engine.", reply_markup=markup)
    
    welcome = f"<b>🔥 HERMES ENGINE PRO v96 ACTIVE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n👤 User: {message.from_user.first_name}\n🚀 System: <code>Online</code>\n━━━━━━━━━━━━━━━━━━━━━━"
    bot.send_photo(message.chat.id, IMG_URL, caption=welcome, reply_markup=get_main_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "my_profile":
        u = users_col.find_one({"user_id": call.from_user.id})
        res = f"<b>👤 PROFILE</b>\n━━━━━━━━━━━━\nID: <code>{u['user_id']}</code>\nTasks: <code>{u['total_tasks']}</code>\nStatus: <code>{u['status'].upper()}</code>"
        bot.edit_message_caption(res, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))
    elif call.data == "verify" and check_join(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    elif call.data == "admin_panel" and call.from_user.id == ADMIN_ID:
        total = users_col.count_documents({})
        bot.edit_message_caption(f"🛠 <b>ADMIN</b>\nTotal Users: {total}\n/stats, /broadcast, /ban", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(ADMIN_ID))

def process_engine(mode, message, status_msg):
    work_dir = f"work_{message.from_user.id}_{int(time.time())}"
    os.makedirs(work_dir, exist_ok=True)
    try:
        import hbctool
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"total_tasks": 1}})
        bot.edit_message_text(f"📥 <b>Downloading...</b>\n{get_progress_bar(30)}", message.chat.id, status_msg.message_id)
        
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        inp = os.path.join(work_dir, "input")
        with open(inp, 'wb') as f: f.write(downloaded)

        if mode == "disasm":
            bot.edit_message_text(f"⚙️ <b>Decompiling...</b>\n{get_progress_bar(60)}", message.chat.id, status_msg.message_id)
            out = os.path.join(work_dir, "out")
            hbctool.disasm(inp, out)
            zip_n = f"Result_{message.from_user.id}.zip"
            with zipfile.ZipFile(zip_n, 'w', zipfile.ZIP_DEFLATED) as z:
                for r, _, fs in os.walk(out):
                    for f in fs: z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), out))
            with open(zip_n, 'rb') as f: bot.send_document(message.chat.id, f, caption="✅ Decompiled!")
            os.remove(zip_n)
        else:
            bot.edit_message_text(f"⚙️ <b>Compiling...</b>\n{get_progress_bar(60)}", message.chat.id, status_msg.message_id)
            ext = os.path.join(work_dir, "ext")
            with zipfile.ZipFile(inp, 'r') as z: z.extractall(ext)
            bundle = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(ext, bundle)
            with open(bundle, 'rb') as f: bot.send_document(message.chat.id, f, caption="✅ Compiled!")

        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, status_msg.message_id)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_eng(message):
    if not check_join(message.from_user.id) or not message.reply_to_message: return
    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status)).start()

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    users = users_col.find({})
    count = 0
    for u in users:
        try:
            if message.reply_to_message:
                bot.copy_message(u['user_id'], message.chat.id, message.reply_to_message.message_id)
            else:
                bot.send_message(u['user_id'], f"📢 <b>Announcement:</b>\n\n{message.text.split('/broadcast ')[1]}")
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {count} users.")

if __name__ == "__main__":
    bootstrap_engine()
    print("✨ Bot Started!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
