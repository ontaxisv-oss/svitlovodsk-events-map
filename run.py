import asyncio
import os
import sys
from aiohttp import web, ClientSession

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database
import parser
from server import create_app, set_bot_instance

RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{config.WEB_SERVER_PORT}")

async def keep_alive_loop():
    """Пінгує сервер кожні 10 хвилин щоб Render не засинав"""
    await asyncio.sleep(60)  # Чекаємо 1 хв після старту
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(f"{RENDER_URL}/api/events", timeout=10) as resp:
                    print(f"💓 Keep-alive ping: HTTP {resp.status}")
        except Exception as e:
            print(f"⚠️ Keep-alive ping failed: {e}")
        await asyncio.sleep(600)  # Кожні 10 хвилин

async def main():
    database.init_db()
    print("==================================================")
    print(f"🚀 Запуск «Карта Подій» місто: {config.CITY_NAME}")
    print(f"📡 Джерело: t.me/{config.SOURCE_CHANNEL} ➡️ Канал: {config.TARGET_CHANNEL}")
    print("==================================================")

    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEB_SERVER_HOST, config.WEB_SERVER_PORT)
    await site.start()

    print(f"🌐 Інтерактивна карта доступна за адресою: http://localhost:{config.WEB_SERVER_PORT}")

    bot_obj = None
    if config.BOT_TOKEN and config.BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        from bot import bot, dp
        bot_obj = bot
        set_bot_instance(bot)
        print("🤖 Telegram-бот успішно підключено!")

    # Запускаємо фоновий парсер повідомлень
    asyncio.create_task(parser.start_parser_loop(bot_instance=bot_obj))

    # Keep-alive: пінгуємо себе кожні 10 хвилин щоб Render не засинав
    asyncio.create_task(keep_alive_loop())
    print(f"💓 Keep-alive запущено (пінг кожні 10 хв → {RENDER_URL})")

    # Запускаємо Pyrogram Userbot для закритих груп якщо вказано API_ID та API_HASH
    if config.API_ID and config.API_HASH:
        import userbot
        asyncio.create_task(userbot.start_userbot())

    if bot_obj:
        from bot import dp
        await dp.start_polling(bot_obj)
    else:
        print("⚠️ BOT_TOKEN не задано. Парсер працює та оновлює веб-карту в автономному режимі.")
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Завершення роботи...")
