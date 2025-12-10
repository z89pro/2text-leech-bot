import os
import re
import sys
import json 
import time
import asyncio
import requests
import subprocess

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, WEBHOOK, PORT
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from aiohttp import web

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from style import Ashu 

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- Code for saving/loading user data ---
USER_DATA_FILE = "user_data.json"
user_targets = {} # Will be loaded from file

def save_user_data():
    """Saves the user_targets dict to a JSON file."""
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(user_targets, f, indent=4)
        print(f"[Bot] Saved user data to {USER_DATA_FILE}")
    except Exception as e:
        print(f"[Bot] Error saving user data: {e}")

def load_user_data():
    """Loads the user_targets dict from a JSON file on startup."""
    global user_targets
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                loaded_data = json.load(f)
                # JSON saves keys as strings, so convert user IDs back to integers
                user_targets = {int(k): v for k, v in loaded_data.items()}
                print(f"[Bot] Loaded user data from {USER_DATA_FILE}")
        else:
            print(f"[Bot] {USER_DATA_FILE} not found. Starting with empty user data.")
            user_targets = {}
    except Exception as e:
        print(f"[Bot] Error loading user data: {e}. Starting fresh.")
        user_targets = {}
# --- End of new code ---


# Define aiohttp routes
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://github.com/AshutoshGoswami24")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    await m.reply_text(
       Ashu.START_TEXT, reply_markup=InlineKeyboardMarkup(
            [
                    [
                    InlineKeyboardButton("✜ ᴀsʜᴜᴛᴏsʜ ɢᴏsᴡᴀᴍɪ 𝟸𝟺 ✜" ,url="https://t.me/AshutoshGoswami24") ],
                    [
                    InlineKeyboardButton("🦋 𝐅𝐨𝐥𝐥𝐨𝐰 𝐌𝐞 🦋" ,url="https://t.me/AshuSupport") ]                               
            ]))
@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("♦ Stopped ♦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


# Command to set the target channel
@bot.on_message(filters.command(["set"]))
async def set_target_handler(bot: Client, m: Message):
    if len(m.command) < 2:
        await m.reply_text(
            "**Usage:** `/set <channel_id_or_username>`\n\n"
            "**Example:** `/set -100123456789` or `/set @my_channel`\n\n"
            "The bot must be an **Admin** in the target channel to post messages."
        )
        return
    
    target_str = m.command[1]
    
    # Handle numeric ID
    if target_str.startswith("-") and target_str[1:].isdigit():
        try:
            target_id = int(target_str)
        except ValueError:
            await m.reply_text("❌ **Error:** Invalid ID format.")
            return
    # Handle username
    elif target_str.startswith("@"):
        target_id = target_str
    # Handle non-numeric or non-username
    else:
        await m.reply_text("❌ **Error:** Please provide a valid channel ID (like `-100123...`) or username (like `@my_channel`).")
        return

    try:
        # Try to get the chat to verify and get the correct ID
        chat = await bot.get_chat(target_id)
        user_targets[m.from_user.id] = chat.id # Store the integer ID
        save_user_data() # NEW: Save data to file
        await m.reply_text(f"✅ **Target channel set!**\n\n**Name:** {chat.title}\n**ID:** `{chat.id}`\n\nAll uploads will now be sent here. Please ensure the bot is an admin in this channel.")
    except Exception as e:
        await m.reply_text(
            f"❌ **Error setting target:** `{e}`\n\n"
            "Please ensure you provided a valid channel ID or username, "
            "and that the bot is already a member of that channel."
        )


@bot.on_message(filters.command(["upload"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text('Send me your `.txt` file ⏍')
    input: Message = await bot.listen(editable.chat.id)

    # --- CHECKS TO FIX THE CRASH ---
    if not input.document:
        await editable.edit("That is not a file. Process cancelled. Please send `/upload` again and send a file.")
        try:
            await input.delete(True)
        except:
            pass
        return  # Stop the function
    
    if not input.document.file_name.endswith(".txt"):
        await editable.edit(f"This is not a `.txt` file (`{input.document.file_name}`). Process cancelled. Please send `/upload` again with a valid `.txt` file.")
        try:
            await input.delete(True)
        except:
            pass
        return  # Stop the function
    # --- END OF CHECKS ---

    x = await input.download()
    await input.delete(True)

    path = f"./downloads/{m.chat.id}"

    try:
       with open(x, "r") as f:
           content = f.read()
       content = content.split("\n")
       links = []
       for i in content:
           if "://" in i: # Ensure it's a link
               links.append(i.split("://", 1))
       os.remove(x)
    except Exception as e:
           await m.reply_text(f"∝ Invalid file input. Error: {e}")
           os.remove(x)
           return
    
   
    await editable.edit(f"**Total links found in txt file:** 🔗 **{len(links)}**\n\nSend the number from where you want to start downloading. (Initial is `1`)")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    # --- Batch Name Question ---
    await editable.edit("∝ Now Please Send Me Your Batch Name")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    

    await editable.edit(Ashu.Q1_TEXT)
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    
    
    # --- NEW: Ask if user wants custom caption ---
    await editable.edit("Do you want to add a custom caption (like 'Robin')?\n\nSend `yes` to add, or `no` to skip.")
    input_choice: Message = await bot.listen(editable.chat.id)
    choice = input_choice.text.lower().strip()
    await input_choice.delete(True)

    MR = "" # Default empty caption
    if choice == 'yes' or choice == 'y':
        # --- Ask for Custom Caption ---
        await editable.edit(Ashu.C1_TEXT)
        input3: Message = await bot.listen(editable.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        highlighter  = f"️ ⁪⁬⁮⁮⁮"
        if raw_text3 == 'Robin':
            MR = highlighter 
        else:
            MR = raw_text3
    # If 'no' or anything else, MR remains "" (empty)
    # --- End of new logic ---

   
    await editable.edit(Ashu.T1_TEXT)
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    if len(links) == 1:
        count = 1
    else:
        try:
            count = int(raw_text)
        except ValueError:
            await m.reply_text("Invalid start number. Defaulting to 1.")
            count = 1


    # --- Check target channel ---
    target_chat_id = user_targets.get(m.from_user.id)
    if not target_chat_id:
        await m.reply_text("⚠️ **No target channel set.**\nI will send files to this chat.\n\nUse `/set <channel_id>` to set a target channel for future uploads.")
        target_chat_id = m.chat.id
    else:
        try:
            target_chat_id = int(target_chat_id) 
            chat = await bot.get_chat(target_chat_id) 
            await m.reply_text(f"✅ **Target channel found!**\n**Name:** {chat.title}\n**ID:** `{chat.id}`\nI will send all uploaded files here.")
        except Exception as e:
            await m.reply_text(f"❌ **Error accessing target channel:** `{e}`\nPlease check the ID/username and ensure the bot is an **Admin** in the target channel.\n\nDefaulting to this chat for now.")
            target_chat_id = m.chat.id
    # --- End of check ---


    try:
        for i in range(count - 1, len(links)):

            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","") # .replace("mpd","m3u8")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']

            elif '/master.mpd' in url:
             id =  url.split("/")[-2]
             url =  "https://d26g5bnklkwsh4.cloudfront.net/" + id + "/master.m3u8"

            # name1 is the raw name from the text file
            name1 = links[i][0].replace("\t", "").strip()
            
            # name is the cleaned version for the file
            name_for_file = name1.replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name_for_file[:60]}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                # --- AUTOMATIC CAPTION (MR is added if you chose 'yes') ---
                # We use 'name1' (raw name) for the caption
                cc = f'**[ 🎥 ] Vid_ID:** {str(count).zfill(3)}. {name1}{MR}.mkv\n✉️ 𝐁𝐚ᴛᴄʜ » **{raw_text0}**'
                cc1 = f'**[ 📁 ] Pdf_ID:** {str(count).zfill(3)}. {name1}{MR}.pdf \n✉️ 𝐁𝐚ᴛᴄʜ » **{raw_text0}**'
                
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        # Send to target_chat_id
                        copy = await bot.send_document(chat_id=target_chat_id, document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        # Use new async download function for PDF as well
                        prog = await m.reply_text(f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐏𝐃𝐅 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » `{name}.pdf`")
                        res_file = await helper.download_video(url, cmd, f"{name}.pdf", prog)
                        
                        if res_file == False: # Check if download failed
                             await prog.edit(f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n⌘ 𝐍𝐚𝐦𝐞 » {name}.pdf\n⌘ 𝐋𝐢𝐧𝐤 » `{url}`")
                             continue # Skip to next link
                        
                        await prog.delete(True)
                        # Send to target_chat_id
                        copy = await bot.send_document(chat_id=target_chat_id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                else:
                    Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » `{name}\n⌨ 𝐐𝐮𝐥𝐢ᴛʏ » {raw_text2}`\n\n**🔗 𝐔𝐑𝐋 »** `{url}`"
                    prog = await m.reply_text(Show)
                    # Pass 'prog' message to download_video to show live progress
                    res_file = await helper.download_video(url, cmd, name, prog)
                    filename = res_file
                    
                    if res_file == False: # Check if download failed
                        await prog.edit(f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n⌘ 𝐍𝐚𝐦𝐞 » {name}\n⌘ 𝐋𝐢𝐧𝐤 » `{url}`")
                        continue # Skip to next link

                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog, target_chat_id)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n{str(e)}\n⌘ 𝐍𝐚𝐦ᴇ » {name}\n⌘ 𝐋𝐢𝐧𝐤 » `{url}`"
                )
                continue

    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("✅ Successfully Done")

async def main():
    if WEBHOOK:
        # Start the web server
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

if __name__ == "__main__":
    load_user_data() # NEW: Load data on startup
    print("""
    █░█░█ █▀█ █▀█ █▀▄ █▀▀ █▀█ ▄▀█ █▀▀ ▀█▀     ▄▀█ █▀ █░█ █░█ ▀█▀ █▀█ █▀ █░█   
    ▀▄▀▄▀ █▄█ █▄█ █▄▀ █▄▄ █▀▄ █▀█ █▀░ ░█░     █▀█ ▄█ █▀█ █▄█ ░█░ █▄█ ▄█ █▀█ """)

    # Start the bot and web server concurrently
    async def start_bot():
        await bot.start()

    async def start_web():
        await main()

    loop = asyncio.get_event_loop()
    try:
        # Create tasks to run bot and web server concurrently
        loop.create_task(start_bot())
        loop.create_task(start_web())

        # Keep the main thread running until all tasks are complete
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        loop.stop()
