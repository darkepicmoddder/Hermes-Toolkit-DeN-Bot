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
    btn1 = types.InlineKeyboardButton("📂 My Profile", callback_data="my_profile")
    btn2 = types.InlineKeyboardButton("📜 Commands", callback_data="help_cmd")
    btn3 = types.InlineKeyboardButton("📢 Channel", url=CHANNEL_URL)
    btn4 = types.InlineKeyboardButton("👤 Developer", url="https://t.me/DarkEpicModderBD0x1")
    markup.add(btn1, btn2, btn3, btn4)
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"))
    return markup

# --- DATABASE LOGIC ---
def sync_user(user):
    user_data = users_col.find_one({"user_id": user.id})
    if not user_data:
        user_data = {
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "N/A",
            "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "total_tasks": 0
        }
        users_col.insert_one(user_data)
    else:
        users_col.update_one({"user_id": user.id}, {"$set": {"last_seen": datetime.now()}})
    return user_data

def is_banned(user_id):
    u = users_col.find_one({"user_id": user_id})
    return u.get("status") == "banned" if u else False

def check_join(user_id):
    if user_id == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- ENGINE SETUP ---
def bootstrap_engine():
    try:
        if os.path.exists(WHL_FILE):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", WHL_FILE])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "hbctool"])
        import hbctool.hbc
        if 96 not in hbctool.hbc.HBC:
            latest_v = max(hbctool.hbc.HBC.keys())
            hbctool.hbc.HBC[96] = hbctool.hbc.HBC[latest_v]
    except: pass

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if is_banned(message.from_user.id):
        return bot.reply_to(message, "🚫 <b>You are banned from using this bot.</b>")
    
    sync_user(message.from_user)
    
    welcome_text = (
        f"<b>🔥 HERMES ENGINE PRO v96 ACTIVE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {message.from_user.first_name}\n"
        f"🚀 <b>Engine:</b> <code>Hermes Decompiler</code>\n"
        f"🛡 <b>Access:</b> <code>Premium Authorized</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Status: System Online and Ready.</i>"
    )
    
    if check_join(message.from_user.id):
        bot.send_photo(message.chat.id, IMG_URL, caption=welcome_text, reply_markup=get_main_keyboard(message.from_user.id))
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, IMG_URL, caption="<b>⚠️ ACCESS DENIED!</b>\nPlease join our official channel to unlock the engine services.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if call.data == "my_profile":
        u = users_col.find_one({"user_id": user_id})
        profile = (
            f"<b>👤 PREMIUM USER PROFILE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{u['user_id']}</code>\n"
            f"🏷 Name: <b>{u['name']}</b>\n"
            f"📅 Joined: <code>{u['joined_at']}</code>\n"
            f"⚡ Tasks: <code>{u['total_tasks']}</code>\n"
            f"💎 Status: <pre>{u['status'].upper()}</pre>"
        )
        bot.edit_message_caption(profile, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(user_id))
    
    elif call.data == "help_cmd":
        help_text = (
            "<b>📥 ENGINE COMMANDS</b>\n\n"
            "⚡ <code>/disasmdem</code> - Reply to index.android.bundle\n"
            "⚡ <code>/asmdem</code> - Reply to your zip folder\n"
            "⚡ <code>/start</code> - Refresh session\n\n"
            "<i>Note: Keep file names standard for best results.</i>"
        )
        bot.edit_message_caption(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(user_id))

    elif call.data == "verify":
        if check_join(user_id):
            bot.answer_callback_query(call.id, "✅ Access Granted!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Verification Failed! Please join the channel first.", show_alert=True)

    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        total = users_col.count_documents({})
        adm_text = (
            f"<b>🛠 ADMIN DASHBOARD</b>\n\n"
            f"👥 Total Users: <code>{total}</code>\n"
            f"🛰 Server: <code>Running v2.0</code>\n\n"
            f"<b>Commands:</b>\n"
            f"• <code>/stats</code> - User details\n"
            f"• <code>/broadcast</code> - Send msg/image\n"
            f"• <code>/ban [ID]</code> - Restrict user"
        )
        bot.edit_message_caption(adm_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(user_id))

# --- CORE ENGINE LOGIC ---
def process_engine(mode, message, status_msg):
    work_id = f"{message.from_user.id}_{int(time.time())}"
    work_dir = f"workspace_{work_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        import hbctool
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"total_tasks": 1}})
        
        # Download Phase
        bot.send_chat_action(message.chat.id, 'typing')
        bot.edit_message_text(f"📥 <b>Downloading File...</b>\n{get_progress_bar(20)}", message.chat.id, status_msg.message_id)
        
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        input_file = os.path.join(work_dir, "input_data")
        with open(input_file, 'wb') as f: f.write(downloaded)

        if mode == "disasm":
            bot.edit_message_text(f"⚙️ <b>Engine: Decompiling...</b>\n{get_progress_bar(50)}", message.chat.id, status_msg.message_id)
            out_path = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out_path)
            
            bot.edit_message_text(f"📦 <b>Packing Result...</b>\n{get_progress_bar(80)}", message.chat.id, status_msg.message_id)
            zip_name = f"Result_{message.from_user.id}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for r, _, fs in os.walk(out_path):
                    for f in fs: z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), out_path))
            
            bot.send_chat_action(message.chat.id, 'upload_document')
            with open(zip_name, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Decompiled successfully by Hermes Engine.</b>")
            os.remove(zip_name)

        else: # Assemble
            bot.edit_message_text(f"⚙️ <b>Engine: Assembling...</b>\n{get_progress_bar(50)}", message.chat.id, status_msg.message_id)
            extract_dir = os.path.join(work_dir, "extract")
            with zipfile.ZipFile(input_file, 'r') as z: z.extractall(extract_dir)
            
            bundle_out = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(extract_dir, bundle_out)
            
            bot.edit_message_text(f"📤 <b>Sending Bundle...</b>\n{get_progress_bar(90)}", message.chat.id, status_msg.message_id)
            bot.send_chat_action(message.chat.id, 'upload_document')
            with open(bundle_out, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Compiled successfully by Hermes Engine.</b>")

        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Process Error:</b>\n<code>{str(e)}</code>", message.chat.id, status_msg.message_id)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_engine_commands(message):
    if not check_join(message.from_user.id) or is_banned(message.from_user.id):
        return bot.reply_to(message, "⚠️ Access Denied. Check Join Status.")
    
    if not message.reply_to_message or not message.reply_to_message.document:
        return bot.reply_to(message, "❌ <b>Error:</b> Please reply to a File (bundle/zip).")
    
    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing Hermes Engine...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status)).start()

# --- ADMIN FUNCTIONS ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id != ADMIN_ID: return
    
    users = users_col.find({})
    count = 0
    
    # Broadcast based on reply
    if message.reply_to_message:
        for u in users:
            try:
                bot.copy_message(u['user_id'], message.chat.id, message.reply_to_message.message_id)
                count += 1
            except: pass
    else:
        msg_text = message.text.replace("/broadcast ", "")
        if not msg_text or msg_text == "/broadcast":
            return bot.reply_to(message, "Usage: <code>/broadcast text</code> OR reply to a photo/msg with <code>/broadcast</code>")
        for u in users:
            try:
                bot.send_message(u['user_id'], f"📢 <b>ANNOUNCEMENT</b>\n\n{msg_text}")
                count += 1
            except: pass
            
    bot.send_message(ADMIN_ID, f"✅ Broadcast finished. Sent to {count} users.")

@bot.message_handler(commands=['stats'])
def stats_handler(message):
    if message.from_user.id != ADMIN_ID: return
    total = users_col.count_documents({})
    tasks = list(users_col.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total_tasks"}}}]))
    total_tasks = tasks[0]['total'] if tasks else 0
    
    res = (
        f"📊 <b>LIVE STATISTICS</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Total Users: <code>{total}</code>\n"
        f"Total Tasks: <code>{total_tasks}</code>\n"
        f"DB Status: <code>Connected ✅</code>"
    )
    bot.send_message(ADMIN_ID, res)

@bot.message_handler(commands=['ban'])
def ban_handler(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        users_col.update_one({"user_id": target_id}, {"$set": {"status": "banned"}})
        bot.reply_to(message, f"🚫 User {target_id} has been banned.")
    except:
        bot.reply_to(message, "Usage: <code>/ban USER_ID</code>")

# --- AUTO RESTART SYSTEM ---
def auto_restart():
    time.sleep(14400) # Restart every 4 hours to keep memory clean
    os._exit(0)

if __name__ == "__main__":
    bootstrap_engine()
    threading.Thread(target=auto_restart, daemon=True).start()
    print("✨ Hermes Bot Premium v2.0 Started!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)  recent = users_col.find().sort("_id", -1).limit(5)
    
    res = f"📊 <b>BOT STATISTICS</b>\n\nTotal: {total}\nBanned: {banned}\n\n<b>Recent:</b>\n"
    for r in recent: res += f"- {r['name']} ({r['user_id']})\n"
    bot.send_message(ADMIN_ID, res)

# --- 24/7 AUTO RESTART ---
def auto_restart():
    time.sleep(20000) # 5.5 hours
    os._exit(0)

if __name__ == "__main__":
    bootstrap_engine()
    threading.Thread(target=auto_restart, daemon=True).start()
    print("✨ Bot Started Successfully!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
