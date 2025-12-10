import os
import time
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
import re # Import regex
import math # Import math

from utils import progress_bar, Timer, hrt, hrb # Import Timer, hrt, hrb

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait


def duration(filename):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)
    except Exception:
        return 0 # Return 0 if duration can't be fetched
    
def exec(cmd):
        process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = process.stdout.decode()
        print(output)
        return output
        #err = process.stdout.decode()
def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)
async def aio(url,name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url,name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka



def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info


def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({f'{i[2]}':f'{i[0]}'})
            except:
                pass
    return new_info


# --- FUNCTION TO PARSE ARIA2C PROGRESS ---
def_dl_text = ' `╭─⌯══⟰ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟰══⌯──★ \n├⚡ {progress_bar}|﹝{percent}﹞ \n├🚀 Speed » {speed} \n├📟 Processed » {processed} \n├🧲 Size - ETA » {total} - {eta} \n`├𝐁𝐲 » 𝐖𝐃 𝐙𝐎𝐍𝐄\n╰─══ ✪ @Opleech_WD ✪ ══─★\n'
timer = Timer() # Add timer to avoid floodwait

async def parse_aria_progress(line, prog_message, start_time):
    # Regex to parse aria2c output
    # e.g., [#d3e691 1.7GiB/2.3GiB(72%) CN:16 DL:10MiB/s ETA:54s]
    pattern = r"\[#.{6}\s(.*?)\/(.*?)\((.*?)\).+DL:\s*(.*?)\sETA:\s*(.*?)\]"
    match = re.search(pattern, line)
    
    if not match:
        return

    if timer.can_send(): # Check if 5 seconds have passed
        try:
            processed_str = match.group(1)
            total_str = match.group(2)
            percent_str = match.group(3)
            speed_str = match.group(4)
            eta_str = match.group(5)
            
            # Helper to convert size strings (e.g., 1.7GiB) to bytes
            def size_to_bytes(size_str):
                if not size_str: return 0
                size_str = size_str.strip()
                if "KiB" in size_str:
                    return float(size_str.replace("KiB", "")) * 1024
                elif "MiB" in size_str:
                    return float(size_str.replace("MiB", "")) * 1024 * 1024
                elif "GiB" in size_str:
                    return float(size_str.replace("GiB", "")) * 1024 * 1024 * 1024
                elif "B" in size_str:
                    return float(size_str.replace("B", ""))
                return 0

            current = size_to_bytes(processed_str)
            total = size_to_bytes(total_str)
            
            if total == 0:
                return # Avoid division by zero

            bar_length = 11
            completed_length = int(current * bar_length / total)
            remaining_length = bar_length - completed_length
            progress_bar_str = "◆" * completed_length + "◇" * remaining_length

            # Format the output similar to upload
            text_to_send = def_dl_text.format(
                progress_bar=progress_bar_str,
                percent=percent_str,
                speed=f"{speed_str}/s",
                processed=processed_str,
                total=total_str,
                eta=eta_str
            )

            await prog_message.edit_text(text_to_send)
        
        except FloodWait as e:
            time.sleep(e.x) # Wait if we get floodwaited
        except Exception as e:
            print(f"Error parsing progress: {e}\nLine: {line}")


# --- MODIFIED 'run' FUNCTION to read stdout line-by-line ---
async def run(cmd, prog_message: Message):
    start_time = time.time()
    
    # This is the corrected command
    cmd_with_progress = cmd 
    
    proc = await asyncio.create_subprocess_shell(
        cmd_with_progress,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    while proc.returncode is None: # While process is running
        line = await proc.stdout.readline()
        if not line:
            break
        line = line.decode('utf-8').strip()
        if line:
            await parse_aria_progress(line, prog_message, start_time)
    
    # Wait for process to finish completely
    await proc.wait() 

    if proc.returncode == 0:
        return proc # Success
    else:
        # Read stderr if error
        stderr = await proc.stderr.read()
        print(f"Download Error: {stderr.decode()}")
        return False # Failure

    
# --- THIS IS THE FIX ---
def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name): # Removed the period before 'file_name'
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


# --- 'download_video' function ---
async def download_video(url, cmd, name, prog_message: Message):
    
    download_cmd = f'{cmd} --progress -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32 --console-log-level=warn --summary-interval=1"'
    
    global failed_counter
    print(download_cmd)
    logging.info(download_cmd)
    
    k = await run(download_cmd, prog_message) # Pass message to 'run'
    
    if k is False:
        return False # Return False to indicate download failure

    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        await download_video(url, cmd, name, prog_message) # Recursive call
        
    if k.returncode != 0:
        return False # Return False to indicate download failure

    failed_counter = 0
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        
        # This part handles PDF downloads as well
        if ".pdf" in name and os.path.isfile(f"{name}"):
            return name

        name_without_ext = name.split(".")[0]
        if os.path.isfile(f"{name_without_ext}.mkv"):
            return f"{name_without_ext}.mkv"
        elif os.path.isfile(f"{name_without_ext}.mp4"):
            return f"{name_without_ext}.mp4"
        elif os.path.isfile(f"{name_without_ext}.mp4.webm"):
            return f"{name_without_ext}.mp4.webm"

        return name
    except FileNotFoundError as exc:
        return os.path.isfile.splitext[0] + "." + "mp4"


async def send_doc(bot: Client, m: Message,cc,ka,cc1,prog,count,name):
    reply = await m.reply_text(f"Uploading » `{name}`")
    time.sleep(1)
    start_time = time.time()
    await m.reply_document(ka,caption=cc1)
    count+=1
    await reply.delete (True)
    time.sleep(1)
    os.remove(ka)
    time.sleep(3) 


# --- 'send_vid' function ---
async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog, target_chat_id: int):
    # This will delete the "Downloading" message
    if prog:
        await prog.delete(True)
        
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
    
    # Reply to the user who started the command
    reply = await m.reply_text(f"**⥣ Uploading ...** » `{name}`")
    
    try:
        if thumb == "no":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb
    except Exception as e:
        await m.reply_text(str(e)) # This reply goes to the user
        thumbnail = f"{filename}.jpg" # Fallback

    # Ensure thumbnail exists
    if not os.path.isfile(thumbnail):
        thumbnail = f"{filename}.jpg"
        
    # Ensure thumbnail is not empty
    thumbnail_to_use = None
    if os.path.isfile(thumbnail) and os.path.getsize(thumbnail) > 0:
        thumbnail_to_use = thumbnail
    else:
        try:
            if os.path.isfile(thumbnail):
                os.remove(thumbnail) # Remove empty or invalid file
        except:
            pass

    dur = int(duration(filename))
    start_time = time.time()

    try:
        # Use bot.send_video with the target_chat_id
        await bot.send_video(
            chat_id=target_chat_id,
            video=filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail_to_use,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time) # Progress bar updates the user's message
        )
    except Exception as e:
        print(f"Video upload failed: {e}. Trying as document.")
        # Use bot.send_document with the target_chat_id as a fallback
        await bot.send_document(
            chat_id=target_chat_id,
            document=filename,
            caption=cc,
            thumb=thumbnail_to_use,
            progress=progress_bar,
            progress_args=(reply, start_time) # Progress bar updates the user's message
        )
        
    os.remove(filename)

    if thumbnail_to_use and os.path.isfile(thumbnail_to_use):
        os.remove(thumbnail_to_use)
        
    await reply.delete (True)
