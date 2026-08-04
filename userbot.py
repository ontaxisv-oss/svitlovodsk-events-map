import asyncio
import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database
import parser

# Ініціалізація Pyrogram Client
app = None
if config.API_ID and config.API_HASH:
    app = Client(
        config.USERBOT_SESSION,
        api_id=config.API_ID,
        api_hash=config.API_HASH
    )

if app:
    @app.on_message(filters.group | filters.channel | filters.private)
    async def handle_userbot_message(client: Client, message: Message):
        # Отримуємо текст повідомлення або підпис під фото
        text = message.text or message.caption or ""
        text = text.strip()

        if not text:
            return

        # Перевірка чи це повідомлення з цільової групи/каналу або містить ключові слова
        chat_username = message.chat.username or ""
        chat_title = message.chat.title or "Група"

        # Перевірка статусу та локації
        status = parser.detect_status(text)
        loc_name, lat, lng = parser.detect_location(text)

        title = f"{loc_name} ({config.STATUSES[status]['title']})"

        # 1. Зберігаємо подібну метку в базу даних веб-карти
        new_event = database.add_event(
            status=status,
            title=title,
            description=text,
            lat=lat,
            lng=lng,
            author_name=f"Userbot ({chat_title})",
            custom_ttl_hours=config.DEFAULT_EVENT_TTL_HOURS
        )
        print(f"⚡️ [Pyrogram Userbot] Додано нову подію на карту: {title} | Статус: {status}")

        # 2. Публікуємо у цільовий канал @kr_probki
        if config.TARGET_CHANNEL:
            try:
                status_icon = "🟢" if status == "green" else ("🔴" if status == "red" else "🟡")
                channel_text = (
                    f"{status_icon} <b>Нове сповіщення через Юзербот!</b>\n\n"
                    f"📍 <b>Локація:</b> {loc_name}\n"
                    f"💬 <b>Повідомлення:</b> {text}\n\n"
                    f"⏱ <i>Дійсне 4 години (подовження/скорочення голосуванням)</i>\n"
                    f"🌐 <b>Карта:</b> {config.PUBLIC_URL}"
                )
                await client.send_message(config.TARGET_CHANNEL, channel_text)
                print(f"📢 [Pyrogram Userbot] Відправлено у канал {config.TARGET_CHANNEL}")
            except Exception as e:
                print(f"⚠️ [Pyrogram Userbot] Помилка надсилання у канал {config.TARGET_CHANNEL}: {e}")

async def start_userbot():
    if not app:
        print("ℹ️ Pyrogram Userbot не налаштовано (API_ID та API_HASH порожні в config.py).")
        return
    
    print("🚀 Запуск Pyrogram Userbot...")
    await app.start()
    print("✅ Pyrogram Userbot успішно підключено та слухає повідомлення закритих груп!")

if __name__ == "__main__":
    if app:
        app.run()
    else:
        print("Вкажіть TELEGRAM_API_ID та TELEGRAM_API_HASH у config.py або змінних середовища.")
