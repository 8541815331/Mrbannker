import logging
import os
import requests
import time
import string
import random
import yaml
import asyncio
import re

from aiogram import Bot, Dispatcher, types, executor
from aiogram.utils.exceptions import Throttled
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bs4 import BeautifulSoup as bs


# Load configuration from config.yml
with open("config.yml", "r") as config_file:
    CONFIG = yaml.safe_load(config_file)

TOKEN = os.getenv("TOKEN", CONFIG["token"])
BLACKLISTED = os.getenv("BLACKLISTED", CONFIG["blacklisted"]).split()
PREFIX = os.getenv("PREFIX", CONFIG["prefix"])
OWNER = int(os.getenv("OWNER", CONFIG["owner"]))
ANTISPAM = int(os.getenv("ANTISPAM", CONFIG["antispam"]))

# Initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get bot info
async def get_bot_info():
    bot_info = await bot.get_me()
    return bot_info.username, bot_info.first_name, bot_info.id

BOT_USERNAME, BOT_NAME, BOT_ID = asyncio.run(get_bot_info())

# Use rotating proxy if needed
PROXIES = {
    "http": "http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/",
    "https": "http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/",
}

# Random Data Generator
letters = string.ascii_lowercase
First = "".join(random.choice(letters) for _ in range(6))
Last = "".join(random.choice(letters) for _ in range(6))
PWD = "".join(random.choice(letters) for _ in range(10))
Name = f"{First} {Last}"
Email = f"{First}.{Last}@gmail.com"
UA = "Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0"


async def is_owner(user_id):
    return user_id == OWNER


async def is_card_valid(card_number: str) -> bool:
    return (
        sum(
            map(
                lambda n: n[1] + (n[0] % 2 == 0) * (n[1] - 9 * (n[1] > 4)),
                enumerate(map(int, card_number[:-1])),
            )
        )
        + int(card_number[-1])
    ) % 10 == 0


# /start & /help command
@dp.message_handler(commands=["start", "help"], commands_prefix=PREFIX)
async def help_command(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "Bot Source", url="https://www.instagram.com/finestofmykind"
    )
    keyboard_markup.row(btn)

    FIRST = message.from_user.first_name
    msg = f"""
Hello {FIRST}, I'm {BOT_NAME}.
You can find my Boss <a href="tg://user?id={OWNER}">HERE</a>.
Commands: /chk /info /bin
"""
    await message.answer(msg, reply_markup=keyboard_markup, disable_web_page_preview=True)


# /info command
@dp.message_handler(commands=["info", "id"], commands_prefix=PREFIX)
async def user_info(message: types.Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.reply(
        f"""
<b>USER INFO</b>
<b>USER ID:</b> <code>{user.id}</code>
<b>USERNAME:</b> @{user.username}
<b>FIRSTNAME:</b> {user.first_name}
<b>BOT:</b> {user.is_bot}
<b>BOT-OWNER:</b> {await is_owner(user.id)}
"""
    )


# /bin command (Fixed)
@dp.message_handler(commands=["bin"], commands_prefix=PREFIX)
async def bin_lookup(message: types.Message):
    await message.answer_chat_action("typing")
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    BIN = message.text[len("/bin "):].strip()

    if len(BIN) < 6:
        return await message.reply("❌ Send a valid BIN (6+ digits).")

    try:
        response = requests.get(f"https://bins.ws/search?bins={BIN[:6]}")
        soup = bs(response.text, "html.parser")
        k = soup.find("div", {"class": "page"})

        if k is None:
            return await message.reply("❌ BIN data not found. The website may have changed or blocked the request.")

        info_text = k.text[62:].strip()
        INFO = f"""
{info_text}
SENDER: <a href="tg://user?id={ID}">{FIRST}</a>
BOT⇢ @{BOT_USERNAME}
OWNER⇢ <a href="tg://user?id={OWNER}">LINK</a>
"""
        await message.reply(INFO)

    except Exception as e:
        await message.reply(f"❌ Error occurred: {e}")


# /chk command (Fixed)
@dp.message_handler(commands=["chk"], commands_prefix=PREFIX)
async def check_card(message: types.Message):
    await message.answer_chat_action("typing")
    ID = message.from_user.id
    FIRST = message.from_user.first_name

    try:
        await dp.throttle("chk", rate=ANTISPAM)
    except Throttled:
        return await message.reply(f"❌ Too many requests! Blocked for {ANTISPAM} seconds.")

    cc_data = message.reply_to_message.text if message.reply_to_message else message.text[len("/chk "):].strip()

    if not cc_data:
        return await message.reply("❌ No Card provided.")

    x = re.findall(r"\d+", cc_data)
    if len(x) < 4:
        return await message.reply("❌ Invalid card format!")

    ccn, mm, yy, cvv = x[0], x[1], x[2], x[3]

    if len(ccn) < 15 or len(ccn) > 16:
        return await message.reply("❌ Invalid card number.")

    BIN = ccn[:6]
    if BIN in BLACKLISTED:
        return await message.reply("❌ BLACKLISTED BIN!")

    if not await is_card_valid(ccn):
        return await message.reply("❌ Invalid card (Luhn algorithm failed).")

    await message.reply(f"✅ Card format is valid. BIN: {BIN}")


# Start polling
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
