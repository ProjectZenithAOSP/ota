#!/usr/bin/env python
#
# Python script to post updates in a Telegram Group for Project Zenith AOSP.
# Automatically checks for new updates and posts them.
# Intended to run on every repository push.

#Copyright (C) 2024 PrajjuS <theprajjus@gmail.com>
# Copyright (C) 2025 Project Zenith
# Credits: Ashwin DS <astroashwin@outlook.com>
# Licensed under the GNU General Public License, version 3 or later.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>

import telebot
import os
import json
import datetime
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from time import sleep
from github import Github
from NoobStuffs.libtelegraph import TelegraphHelper

# Get configurations from environment variables
def getConfig(config_name: str):
    return os.getenv(config_name)

try:
    BOT_TOKEN = getConfig("BOT_TOKEN")
    CHAT_ID = getConfig("CHAT_ID")
    PRIV_CHAT_ID = getConfig("PRIV_CHAT_ID")
except KeyError:
    print("Please set all required configurations. Exiting...")
    exit(0)

# Get the version of Project Zenith to check for updates
def getZenithVersion():
    VENDOR_REPO = "ProjectZenithAOSP/vendor_zenith"
    VERSION_FILE = "config/version.mk"
    VERSION_REGEX = r"ZENITH_DISPLAY_VERSION := (.*)"
    g = Github(getConfig("GH_TOKEN"))
    repo = g.get_repo(VENDOR_REPO)
    content = repo.get_contents(VERSION_FILE).decoded_content.decode()
    version = re.search(VERSION_REGEX, content).group(1) if re.search(VERSION_REGEX, content) else None
    return version

ZENITH_VERSION_CHECK = getZenithVersion()
BANNER_PATH = "./banners/banner.png"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
telegraph = TelegraphHelper(
    author_name="Project-Zenith Bot",
    author_url="https://t.me/ProjectZenithbot",
    domain="graph.org"
)

# File directories
jsonDir = "devices"
idDir = ".github/scripts"

# Store IDs in a file for comparison
def update(IDs):
    with open(f"{idDir}/file_ids.txt", "w+") as log:
        for ids in IDs:
            log.write(f"{str(ids)}\n")

# Return IDs of all latest files from JSON files
def get_new_id():
    files = [f for f in os.listdir(jsonDir) if f.endswith('.json')]
    file_id = []
    for file in files:
        with open(f"{jsonDir}/{file}", "r") as f:
            data = json.loads(f.read())['response'][0]
            file_id.append(data['md5'])
    return file_id

# Return previous IDs
def get_old_id():
    if not os.path.exists(f"{idDir}/file_ids.txt"):
        return []
    with open(f"{idDir}/file_ids.txt", "r") as log:
        return [line.strip() for line in log.readlines()]

# Get difference between old and new IDs
def get_diff(new_id, old_id):
    return list(set(new_id) - set(old_id))

# Get details for a specific file ID
def get_info(ID):
    files = [f for f in os.listdir(jsonDir) if f.endswith('.json')]
    for file in files:
        with open(f"{jsonDir}/{file}", "r") as f:
            data = json.loads(f.read())['response'][0]
            if data['md5'] == ID:
                with open(f"{jsonDir}/{file}", "r") as f:
                    info = json.loads(f.read())['response'][0]
                    return {
                        "version": info['version'],
                        "oem": info['oem'],
                        "device_name": info['device'],
                        "codename": file.split('.')[0],
                        "maintainer": info['maintainer'],
                        "datetime": datetime.datetime.fromtimestamp(int(info['timestamp'])),
                        "download": info['download'],
                        "size": round(int(info['size']) / 1_000_000_000, 2),
                        "md5": info['md5'],
                        "xda": info['forum'],
                        "telegram": info['telegram']
                    }

# Prepare Telegram message for a device update
def format_message(info):
    return (
        f"<b>Project Zenith | OFFICIAL | Android 15 (V)</b>\n\n"
        f"<b>Device:</b> <code>{info['oem']} {info['device_name']} ({info['codename']})</code>\n"
        f"<b>Maintainer:</b> <a href='https://t.me/{info['telegram']}'>{info['maintainer']}</a>\n"
        f"<b>Version:</b> <code>{info['version']}</code>\n"
        f"<b>Build Date:</b> <code>{info['datetime']} UTC</code>\n\n"
        f"<b>Download:</b> <a href='{info['download']}'>Click here</a>\n"
        f"<b>Source Changelogs:</b> <a href='https://github.com/ProjectZenithAOSP/ota/blob/15-qpr1/changelogs/changelog_zenith.txt'>Here</a>\n"
        f"<b>Device Changelogs:</b> <a href='https://github.com/ProjectZenithAOSP/ota/blob/15-qpr1/changelogs/changelog_{info['codename']}.txt'>Here</a>\n\n"
    )

# Send updates to the channel
def tg_message():
    if not get_diff(get_new_id(), get_old_id()):
        print("No new updates found.")
        exit(0)
    for device_id in get_diff(get_new_id(), get_old_id()):
        info = get_info(device_id)
        with open(BANNER_PATH, "rb") as banner:
            bot.send_photo(chat_id=CHAT_ID, photo=banner, caption=format_message(info))
        sleep(5)
    update(get_new_id())

# Log update status in a private group
def tg_log():
    updated_devices = []
    not_updated_devices = []
    for device in get_new_id():
        if device in get_old_id():
            updated_devices.append(device)
        else:
            not_updated_devices.append(device)

    total_devices = len(updated_devices) + len(not_updated_devices)
    text = (
        f"<b>Project Zenith Update Status</b>\n\n"
        f"<b>Total Devices:</b> {total_devices}\n"
        f"<b>Updated:</b> {len(updated_devices)}\n"
        f"<b>Not Updated:</b> {len(not_updated_devices)}\n"
    )
    bot.send_message(chat_id=PRIV_CHAT_ID, text=text)

# Run the script
if __name__ == "__main__":
    tg_message()
    tg_log()
    print("Updates posted successfully.")

