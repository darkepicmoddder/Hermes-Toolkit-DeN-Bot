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

# --- MONGODB CONNECTION ---
raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
client = MongoClient(raw_uri)
db = client['hermes_ultra_db']
users_col = db['users']

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=20)
logging.basicConfig(level=logging.INFO)

# --- DATABASE FUNCTIONS ---
def sync_user(user):
    existing = users_col.find_one({"user_id": user.id})
    if not existing:
        users_col.insert_one({
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "N/A",
            "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "total_tasks": 0
        })
    else:
        users_col.update_one({"user_id": user.id}, {"$set": {"last_seen": datetime.now()}})

def is_banned(user_id):
    user = users_col.find_one({"user_id": user_id})
    return user.get("status") == "banned" if user else False

def increment_task(user_id):
    users_col.update_one({"user_id": user_id}, {"$inc": {"total_tasks": 1}})

# --- ENGINE BOOTSTRAP ---
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

# --- UI HELPERS ---
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

def check_join(user_id):
    if user_id == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if is_banned(message.from_user.id):
        return bot.reply_to(message, "🚫 You are banned from using this bot.")
    
    sync_user(message.from_user)
    
    welcome_text = (
        f"<b>🔥 HERMES ENGINE PRO v96 ACTIVE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Hello, <b>{message.from_user.first_name}!</b>\n"
        f"Welcome to the most advanced Hermes Decompiler/Compiler bot.\n\n"
        f"🚀 <b>Engine Status:</b> <code>Online</code>\n"
        f"🛡 <b>Access:</b> <code>Premium</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Please make sure you have joined our channel to keep using the services.</i>"
    )
    
    if check_join(message.from_user.id):
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(message.from_user.id))
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        bot.send_message(message.chat.id, "<b>⚠️ Access Denied!</b>\nYou must join our channel to use the engine.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "my_profile":
        u = users_col.find_one({"user_id": call.from_user.id})
        profile = (
            f"<b>👤 YOUR PROFILE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"ID: <code>{u['user_id']}</code>\n"
            f"Name: <b>{u['name']}</b>\n"
            f"Joined: <code>{u['joined_at']}</code>\n"
            f"Tasks Done: <code>{u['total_tasks']}</code>\n"
            f"Status: <code>{u['status'].upper()}</code>"
        )
        bot.edit_message_text(profile, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))
    
    elif call.data == "help_cmd":
        help_text = (
            "<b>📥 USER COMMANDS</b>\n\n"
            "⚡ <code>/disasmdem</code> - Reply to index.android.bundle to decompile.\n"
            "⚡ <code>/asmdem</code> - Reply to zip file to compile.\n"
            "⚡ <code>/start</code> - Restart the bot interface.\n\n"
            "<i>Note: Process may take 1-2 mins based on file size.</i>"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))

    elif call.data == "admin_panel" and call.from_user.id == ADMIN_ID:
        total = users_col.count_documents({})
        adm_text = (
            f"<b>🛠 ADMIN DASHBOARD</b>\n\n"
            f"Total Users: <code>{total}</code>\n"
            f"Engine: <code>Hermes v96</code>\n\n"
            f"<b>Admin Commands:</b>\n"
            f"/stats - Full stats\n"
            f"/broadcast - Message all\n"
            f"/ban [ID] - Block user"
        )
        bot.edit_message_text(adm_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))

    elif call.data == "verify":
        if check_join(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Not joined yet!", show_alert=True)

# --- ENGINE PROCESSING (SAFE MULTI-USER) ---
def process_engine(mode, message, status_msg):
    # ইউনিক ওয়ার্কস্পেস তৈরি যাতে ফাইল ওভাররাইট না হয়
    work_id = f"{message.from_user.id}_{int(time.time())}"
    work_dir = f"workspace_{work_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        import hbctool
        increment_task(message.from_user.id)
        
        # Download
        bot.edit_message_text("📥 <b>Downloading file...</b>", message.chat.id, status_msg.message_id)
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        input_file = os.path.join(work_dir, "input_data")
        with open(input_file, 'wb') as f: f.write(downloaded)

        if mode == "disasm":
            bot.edit_message_text("⚙️ <b>Engine: Decompiling (v96)...</b>", message.chat.id, status_msg.message_id)
            out_path = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out_path)
            
            zip_name = f"Result_{work_id}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for r, _, fs in os.walk(out_path):
                    for f in fs: z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), out_path))
            
            with open(zip_name, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Decompiled Successfully!</b>")
            os.remove(zip_name)

        else: # Assemble
            bot.edit_message_text("⚙️ <b>Engine: Assembling (v96)...</b>", message.chat.id, status_msg.message_id)
            extract_dir = os.path.join(work_dir, "extract")
            with zipfile.ZipFile(input_file, 'r') as z: z.extractall(extract_dir)
            
            bundle_out = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(extract_dir, bundle_out)
            
            with open(bundle_out, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Compiled Successfully!</b>")

        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Error:</b>\n<code>{str(e)}</code>", message.chat.id, status_msg.message_id)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_engine(message):
    if not check_join(message.from_user.id) or is_banned(message.from_user.id): return
    if not message.reply_to_message:
        return bot.reply_to(message, "❌ Please reply to a bundle or zip file!")
    
    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status)).start()

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    if not msg_text or msg_text == "/broadcast":
        return bot.reply_to(message, "Usage: <code>/broadcast Hello Users</code>")
    
    users = users_col.find({})
    count = 0
    for u in users:
        try:
            bot.send_message(u['user_id'], f"📢 <b>ANNOUNCEMENT</b>\n\n{msg_text}")
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total = users_col.count_documents({})
    banned = users_col.count_documents({"status": "banned"})
    recent = users_col.find().sort("_id", -1).limit(5)
    
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
