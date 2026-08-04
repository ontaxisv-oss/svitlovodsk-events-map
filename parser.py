import asyncio
import json
import os
import re
import sys
import time
import aiohttp
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PARSED_IDS_FILE = os.path.join(DATA_DIR, "parsed_ids.json")

# Розширена база локацій та координат Світловодська
LOCATION_COORDS = {
    "героїв україни": (49.0560, 33.2250),
    "леніна": (49.0560, 33.2250),
    "дамб": (49.0760, 33.2510),
    "гес": (49.0760, 33.2510),
    "мост": (49.0760, 33.2510),
    "загребл": (49.0480, 33.2390),
    "автостанц": (49.0525, 33.2180),
    "ас": (49.0525, 33.2180),
    "ювілейн": (49.0520, 33.2200),
    "набережн": (49.0600, 33.2300),
    "придніпров": (49.0610, 33.2320),
    "центр": (49.0540, 33.2280),
    "палац культури": (49.0555, 33.2265),
    "парк": (49.0580, 33.2350),
    "рин": (49.0530, 33.2230),
    "базар": (49.0530, 33.2230),
    "магістральн": (49.0500, 33.2150),
    "промислов": (49.0460, 33.2100)
}

def load_parsed_ids():
    if not os.path.exists(PARSED_IDS_FILE):
        return []
    try:
        with open(PARSED_IDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_parsed_ids(parsed_ids):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    # Зберігаємо тільки останні 200 ID
    with open(PARSED_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed_ids[-200:], f, ensure_ascii=False, indent=2)

def detect_status(text):
    text_lower = text.lower().strip()
    
    # 🟢 Зелена тільки якщо в кінці є ключове слово спокою
    green_endings = ["сонце", "спокійно", "☀️", "🌞", "все ок", "чисто", "вільно", "тиша"]
    for kw in green_endings:
        if text_lower.endswith(kw) or text_lower.endswith(kw + ".") or text_lower.endswith(kw + "!"):
            return "green"
    # Також перевіряємо останні 30 символів
    tail = text_lower[-30:]
    for kw in green_endings:
        if kw in tail:
            return "green"
    
    # 🔴 За замовчуванням — червона
    return "red"

def detect_location(text):
    text_lower = text.lower()
    for loc_key, coords in LOCATION_COORDS.items():
        if loc_key in text_lower:
            return loc_key.capitalize(), coords[0], coords[1]
    
    # За замовчуванням центр Світловодська
    return "Світловодськ", config.CITY_CENTER_LAT, config.CITY_CENTER_LNG

async def fetch_channel_messages():
    url = f"https://t.me/s/{config.SOURCE_CHANNEL}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    print(f"⚠️ Парсер: Помилка завантаження сторінки каналу (код {resp.status})")
                    return []
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        message_elements = soup.find_all("div", class_="tgme_widget_message")

        messages = []
        for el in message_elements:
            msg_id = el.get("data-post")
            if not msg_id:
                continue

            text_el = el.find("div", class_="tgme_widget_message_text")
            if not text_el:
                continue

            msg_text = text_el.get_text(separator=" ").strip()
            if not msg_text:
                continue

            messages.append({
                "id": msg_id,
                "text": msg_text
            })

        return messages
    except Exception as e:
        print(f"⚠️ Парсер: Помилка під час зчитування: {e}")
        return []

async def process_new_messages(bot_instance=None):
    parsed_ids = load_parsed_ids()
    messages = await fetch_channel_messages()

    new_count = 0
    for msg in messages:
        if msg["id"] in parsed_ids:
            continue

        parsed_ids.append(msg["id"])
        text = msg["text"]
        
        status = detect_status(text)
        loc_name, lat, lng = detect_location(text)

        title = f"{loc_name} ({config.STATUSES[status]['title']})"
        
        # 1. Додаємо на веб-карту
        new_event = database.add_event(
            status=status,
            title=title,
            description=text,
            lat=lat,
            lng=lng,
            author_name=f"t.me/{config.SOURCE_CHANNEL}",
            custom_ttl_hours=config.DEFAULT_EVENT_TTL_HOURS
        )

        new_count += 1
        print(f"✨ [Парсер] Нова подія з t.me/{config.SOURCE_CHANNEL}: {title} | Status: {status}")

        # 2. Публікуємо у цільовий канал @kr_probki якщо підключено бота
        if bot_instance and config.TARGET_CHANNEL:
            try:
                status_icon = "🟢" if status == "green" else ("🔴" if status == "red" else "🟡")
                
                post_text = (
                    f"{status_icon} <b>Нове сповіщення про ситуацію на дорогах!</b>\n\n"
                    f"📍 <b>Локація:</b> {loc_name}\n"
                    f"💬 <b>Повідомлення:</b> {text}\n\n"
                    f"⏱ <i>Дійсне 4 години (можна подовжити голосуванням на карті)</i>\n"
                    f"📢 Джерело: @{config.SOURCE_CHANNEL}"
                )

                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🗺 Переглянути на Карті Подій", url=config.PUBLIC_URL)
                ]])

                await bot_instance.send_message(config.TARGET_CHANNEL, post_text, parse_mode="HTML", reply_markup=keyboard)
                print(f"📢 [Парсер] Опубліковано у канал {config.TARGET_CHANNEL}")
            except Exception as e:
                print(f"⚠️ Помилка відправки у канал {config.TARGET_CHANNEL}: {e}")

    save_parsed_ids(parsed_ids)
    return new_count

async def start_parser_loop(bot_instance=None):
    print(f"🔄 Фоновий парсер запущено: t.me/{config.SOURCE_CHANNEL} ➡️ {config.TARGET_CHANNEL}")
    while True:
        try:
            await process_new_messages(bot_instance=bot_instance)
        except Exception as e:
            print(f"⚠️ Ошибка в циклі парсера: {e}")
        await asyncio.sleep(config.PARSE_INTERVAL_SEC)
