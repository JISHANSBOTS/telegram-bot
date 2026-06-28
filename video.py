.import os
import sys

# =====================================================================
# 🛠️ AUTO-INSTALLER SYSTEM
# =====================================================================
try:
    import pyrogram
    import tgcrypto
except ImportError:
    print("Required packages nahi mile! Automatic install ho rahe hain...")
    os.system(f"{sys.executable} -m pip install --upgrade pyrogram tgcrypto")
    print("Packages install ho gaye hain! Bot ko restart kiya ja raha hai...")
    os.execv(sys.executable, ['python'] + sys.argv)

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- Configuration ---
API_ID = 36392592                 # Apna Telegram API ID dalo (integer)
API_HASH = "8ac058c4fc648e0cc9b498bbbd21f9c9"   # Apna API Hash dalo
BOT_TOKEN = "8825315897:AAGZaIe7cspjOeSt7-nPuAR5nBtM9ZAVMOI" # BotFather se mila token dalo
SUPER_ADMIN = 8789240020          # Aapki ID (Main Owner)

app = Client("video_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Storage Files & Folders Setup ---
VIDEO_FOLDER = "Video"
USER_FILE = "user.txt"
ADMIN_FILE = "admins.txt"
BAN_FILE = "banned.txt"
CHANNELS_FILE = "channels.txt"
SETTINGS_FILE = "settings.txt"
BUTTON_FILE = "buttons.txt"

for f in [USER_FILE, ADMIN_FILE, BAN_FILE, CHANNELS_FILE, SETTINGS_FILE, BUTTON_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file: pass

if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

# --- Helper Functions (File Based Storage) ---
def load_list(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_to_file(filename, data):
    with open(filename, "a") as f:
        f.write(f"{data}\n")

def rewrite_list(filename, data_list):
    with open(filename, "w") as f:
        for item in data_list:
            f.write(f"{item}\n")

# Settings Management (Referrals)
def get_settings():
    lines = load_list(SETTINGS_FILE)
    settings = {"start_ref": 0, "video_ref": 0}
    for line in lines:
        if ":" in line:
            k, v = line.split(":")
            settings[k] = int(v)
    return settings

def save_settings(k, v):
    settings = get_settings()
    settings[k] = int(v)
    with open(SETTINGS_FILE, "w") as f:
        for key, val in settings.items():
            f.write(f"{key}:{val}\n")

# Referral Counter tracking in user.txt -> format: user_id|referred_by|points
def get_user_data(user_id):
    lines = load_list(USER_FILE)
    for line in lines:
        if line.startswith(str(user_id)):
            parts = line.split("|")
            return {"id": parts[0], "ref_by": parts[1], "points": int(parts[2])}
    return None

def add_new_user(user_id, ref_by="None"):
    if not get_user_data(user_id):
        save_to_file(USER_FILE, f"{user_id}|{ref_by}|0")
        if ref_by != "None" and str(ref_by) != str(user_id):
            # Increament referrer points
            lines = load_list(USER_FILE)
            new_lines = []
            for line in lines:
                if line.startswith(str(ref_by)):
                    parts = line.split("|")
                    pts = int(parts[2]) + 1
                    new_lines.append(f"{parts[0]}|{parts[1]}|{pts}")
                else:
                    new_lines.append(line)
            rewrite_list(USER_FILE, new_lines)

# --- Admin Verifier ---
def is_admin(user_id):
    if user_id == SUPER_ADMIN: return True
    admins = load_list(ADMIN_FILE)
    return str(user_id) in admins

# --- State Trackers ---
admin_states = {}

# =====================================================================
# 🤖 BOT COMMANDS LOGIC
# =====================================================================

# 1. /start Command (With Referral Tracking & Forced Join)
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user_id = message.from_user.id
    
    # Ban check
    if str(user_id) in load_list(BAN_FILE):
        await message.reply_text("❌ Aap is bot se banned hain.")
        return

    # Referral link capture
    ref_by = "None"
    if len(message.command) > 1:
        ref_by = message.command[1]

    add_new_user(user_id, ref_by)
    
    # Forced Channel Check
    channels = load_list(CHANNELS_FILE)
    for ch in channels:
        try:
            member = await client.get_chat_member(ch, user_id)
        except Exception:
            await message.reply_text(f"⚠️ Bot use karne ke liye pehle hamare channel ko join karein:\n👉 {ch}\n\nJoin karne ke baad dobara /start dabayein.")
            return

    settings = get_settings()
    user_info = get_user_data(user_id)
    
    # Check if user meets registration/start referral requirements
    if user_info["points"] < settings["start_ref"]:
        await message.reply_text(
            f"🔒 **Referral Requirement Alert!**\n\n"
            f"Bot start karne ke liye aapko kam se kam **{settings['start_ref']}** referrals chahiye.\n"
            f"Aapke pass abhi **{user_info['points']}** referrals hain.\n\n"
            f"🔗 **Aapka Referral Link:** https://t.me/{client.me.username}?start={user_id}"
        )
        return

    # Success Start Screen
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("Get Video 🎬")]], resize_keyboard=True)
    await message.reply_text("Click on get video 👇", reply_markup=keyboard)


# 2. Get Video Button Handler
@app.on_message(filters.regex("^Get Video 🎬$") & filters.private)
async def get_video_request(client, message: Message):
    user_id = message.from_user.id
    
    if str(user_id) in load_list(BAN_FILE): return

    settings = get_settings()
    user_info = get_user_data(user_id)

    # Check if user meets video download referral requirements
    if user_info["points"] < settings["video_ref"]:
        await message.reply_text(
            f"🔒 **Video Blocked!**\n\n"
            f"Video lene ke liye kam se kam **{settings['video_ref']}** referrals hone chahiye.\n"
            f"Aapke paas: **{user_info['points']}** referrals hain.\n\n"
            f"🔗 **Apna link share karein:** https://t.me/{client.me.username}?start={user_id}"
        )
        return

    # Fetch random/available video from folder
    Video = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(('.mp4', '.mkv', '.avi'))]
    if not Video:
        await message.reply_text("😔 Sorry! Abhi folder me koi video uploaded nahi hai.")
        return

    video_path = os.path.join(VIDEO_FOLDER, Video[0]) # Pehli video bhej raha hai sample ke liye

    # Load custom admin injected buttons underneath the video
    buttons_list = load_list(BUTTON_FILE)
    inline_btns = []
    for btn in buttons_list:
        if "|" in btn:
            name, url = btn.split("|")
            inline_btns.append([InlineKeyboardButton(name.strip(), url=url.strip())])
    
    reply_markup = InlineKeyboardMarkup(inline_btns) if inline_btns else None

    await message.reply_text("⏳ Video load ho rahi hai, please wait...")
    await client.send_video(chat_id=user_id, video=video_path, caption="✨ Aapki Video Ready Hai!", reply_markup=reply_markup)


# 3. Admin Control Panel Panel (/admin)
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id): return

    admin_msg = (
        "⚡ **WELCOME TO PREMIUM ADMIN PANEL** ⚡\n\n"
        "📢 **Broadcast:** `/broadcast` - Sabhi users ko\n"
        "➕ **Admin Manage:** `/addadmin` | `/removeadmin`\n"
        "🎬 **Video Storage:** `/uploadvideo` | `/removevideo` | `/checkvideo`\n"
        "🔗 **Forced Join:** `/forcechanneladd` | `/forcechannelremove` | `/forcechannellist`\n"
        "📊 **Users Info:** `/userlist` | `/banuser` | `/banuserlist`\n"
        "⚙️ **Referral Limits:** `/setstartref` (Value) | `/setvideoref` (Value)\n"
        "🔘 **Custom Links:** `/addbutton` (button name | button url) | `/clearbuttons`"
    )
    await message.reply_text(admin_msg)


# =====================================================================
# 🛠️ ADMIN COMMANDS EXECUTION FUNCTIONS
# =====================================================================

@app.on_message(filters.command("broadcast") & filters.private)
async def admin_broadcast(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "BROADCAST"
    await message.reply_text("📢 Wo text/post bhein jo sabhi ko bhejni hai:")

@app.on_message(filters.command("addadmin") & filters.private)
async def add_admin_cmd(client, message: Message):
    if message.from_user.id != SUPER_ADMIN: return
    admin_states[message.from_user.id] = "ADD_ADMIN"
    await message.reply_text("➕ Naye Admin ki Numerical ID send karein:")

@app.on_message(filters.command("removeadmin") & filters.private)
async def remove_admin_cmd(client, message: Message):
    if message.from_user.id != SUPER_ADMIN: return
    admin_states[message.from_user.id] = "REMOVE_ADMIN"
    await message.reply_text("❌ Jis Admin ko hatana hai uski ID send karein:")

@app.on_message(filters.command("uploadvideo") & filters.private)
async def upload_video_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "UPLOAD_VIDEO"
    await message.reply_text("🎬 Ab bot par koi bhi video file `.mp4` attach karke upload karein:")

@app.on_message(filters.command("removevideo") & filters.private)
async def remove_video_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "REMOVE_VIDEO"
    await message.reply_text("🗑️ Remove karne ke liye video ka exact file name type karein:")

@app.on_message(filters.command("checkvideo") & filters.private)
async def check_video_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    Video = os.listdir(VIDEO_FOLDER)
    if not Video:
        await message.reply_text("📁 Folder khali hai!")
    else:
        await message.reply_text("📂 **Storage Video:**\n\n" + "\n".join([f"🔹 `{v}`" for v in Video]))

@app.on_message(filters.command("forcechanneladd") & filters.private)
async def force_add_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "ADD_CH"
    await message.reply_text("🔗 Channel ka username ya ID bhejo (e.g., `@MyChannel`):")

@app.on_message(filters.command("forcechannelremove") & filters.private)
async def force_rem_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "REM_CH"
    await message.reply_text("❌ Remove karne wale channel ka username type karein:")

@app.on_message(filters.command("forcechannellist") & filters.private)
async def force_list_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    ch = load_list(CHANNELS_FILE)
    await message.reply_text(f"📢 **Forced Channels:**\n\n" + "\n".join(ch) if ch else "Koi channel set nahi hai.")

@app.on_message(filters.command("userlist") & filters.private)
async def userlist_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    users = load_list(USER_FILE)
    await message.reply_text(f"📊 **Total Users Saved in user.txt:** {len(users)}")

@app.on_message(filters.command("banuser") & filters.private)
async def ban_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    admin_states[message.from_user.id] = "BAN"
    await message.reply_text("🚫 Ban karne ke liye user ID send karein:")

@app.on_message(filters.command("banuserlist") & filters.private)
async def banlist_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    bl = load_list(BAN_FILE)
    await message.reply_text("🚫 **Banned Users:**\n" + "\n".join(bl) if bl else "Koi banned nahi hai.")

@app.on_message(filters.command("setstartref") & filters.private)
async def set_start_ref(client, message: Message):
    if not is_admin(message.from_user.id): return
    val = message.text.split(maxsplit=1)[1]
    save_settings("start_ref", val)
    await message.reply_text(f"✅ Bot start karne ke liye minimum referral settings updated to: **{val}**")

@app.on_message(filters.command("setvideoref") & filters.private)
async def set_video_ref(client, message: Message):
    if not is_admin(message.from_user.id): return
    val = message.text.split(maxsplit=1)[1]
    save_settings("video_ref", val)
    await message.reply_text(f"✅ Video lene ke liye minimum referral settings updated to: **{val}**")

@app.on_message(filters.command("addbutton") & filters.private)
async def add_btn_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    try:
        data = message.text.split(maxsplit=1)[1]
        if "|" in data:
            save_to_file(BUTTON_FILE, data)
            await message.reply_text("✅ Naya custom button configuration register ho gaya!")
        else:
            await message.reply_text("❌ Syntax galat hai! Use karein: `/addbutton Name | https://link.com`")
    except IndexError:
        await message.reply_text("❌ Input Khali hai!")

@app.on_message(filters.command("clearbuttons") & filters.private)
async def clear_btn_cmd(client, message: Message):
    if not is_admin(message.from_user.id): return
    open(BUTTON_FILE, 'w').close()
    await message.reply_text("🗑️ Saare buttons clear/remove kar diye gaye hain.")


# =====================================================================
# 📥 ADMIN PROCESS INPUT INPUT HANDLERS
# =====================================================================

@app.on_message(filters.private & ~filters.command(["start", "admin"]))
async def handle_admin_inputs(client, message: Message):
    user_id = message.from_user.id
    state = admin_states.get(user_id)

    if not state: return

    # Clear state instantly after pick
    del admin_states[user_id]

    if state == "BROADCAST":
        users = load_list(USER_FILE)
        sent = 0
        for u in users:
            try:
                uid = u.split("|")[0]
                await message.copy(chat_id=int(uid))
                sent += 1
            except Exception: pass
        await message.reply_text(f"📢 Broadcast Done! Sent to {sent} users.")

    elif state == "ADD_ADMIN":
        save_to_file(ADMIN_FILE, message.text.strip())
        await message.reply_text("✅ User successfully admins.txt list me add ho gaya!")

    elif state == "REMOVE_ADMIN":
        ad_list = load_list(ADMIN_FILE)
        if message.text.strip() in ad_list:
            ad_list.remove(message.text.strip())
            rewrite_list(ADMIN_FILE, ad_list)
            await message.reply_text("❌ Admin successfully removed!")
        else:
            await message.reply_text("Admin ID nahi mili.")

    elif state == "UPLOAD_VIDEO":
        if message.video:
            status = await message.reply_text("📥 Video download hokar `Video/` folder me save ho rahi hai...")
            file_name = message.video.file_name if message.video.file_name else f"video_{message.id}.mp4"
            await message.download(file_name=os.path.join(VIDEO_FOLDER, file_name))
            await status.edit_text(f"✅ Successful! Video saved as `{file_name}` in system storage.")
        else:
            await message.reply_text("❌ Ye video file nahi thi. Mode cancelled.")

    elif state == "REMOVE_VIDEO":
        v_path = os.path.join(VIDEO_FOLDER, message.text.strip())
        if os.path.exists(v_path):
            os.remove(v_path)
            await message.reply_text("🗑️ File successfully removed from folder storage.")
        else:
            await message.reply_text("File name nahi mila. Check spelling.")

    elif state == "ADD_CH":
        save_to_file(CHANNELS_FILE, message.text.strip())
        await message.reply_text("✅ Force Join target channels list me jodh diya gaya hai.")

    elif state == "REM_CH":
        ch_list = load_list(CHANNELS_FILE)
        if message.text.strip() in ch_list:
            ch_list.remove(message.text.strip())
            rewrite_list(CHANNELS_FILE, ch_list)
            await message.reply_text("❌ Force channel removed!")

    elif state == "BAN":
        save_to_file(BAN_FILE, message.text.strip())
        await message.reply_text("🚫 User successfully banned.")

if __name__ == "__main__":
    print("🤖 Premium Video Manager & Referral System Bot Started...")
    app.run()
                                   
