# ╔══════════════════════════════════════════════════════════╗
# ║         КОНФІГУРАЦІЯ КАРТИ ПОДІЙ СВІТЛОВОДСЬК             ║
# ╚══════════════════════════════════════════════════════════╝

import os

# --- ТЕЛЕГРАМ ТА БОТ ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8469860489:AAH2ZC7y7FUeF6wZleI0Z_amSFdVxk4mY8w")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.isdigit()]
SOURCE_CHANNEL = "kr_probki"      # Джерело: https://t.me/kr_probki
TARGET_CHANNEL = "@kr_probki"   # Канал для публікацій
PARSE_INTERVAL_SEC = 30         # Перевірка нових повідомлень кожні 30 секунд

# --- PYROGRAM USERBOT (Для закритих груп та каналів) ---
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))      # Вставте ваш API_ID сюди
API_HASH = os.getenv("TELEGRAM_API_HASH", "")        # Вставте ваш API_HASH сюди
USERBOT_SESSION = "svitlovodsk_userbot"

# --- НАЛАШТУВАННЯ МІСТА СВІТЛОВОДСЬК ---
CITY_NAME = "Світловодськ"
COUNTRY_NAME = "Україна"

# Координати центру Світловодська
CITY_CENTER_LAT = 49.054000
CITY_CENTER_LNG = 33.228000
DEFAULT_ZOOM = 13

# --- ПАРАМЕТРИ ПОДІЙ ТА ЧАСУ (TTL) ---
DEFAULT_EVENT_TTL_HOURS = 0.25  # Час життя події за замовчуванням (15 хвилин)
DEFAULT_EVENT_TTL_MINUTES = 15 # 15 хвилин
UPVOTE_EXTEND_MINUTES = 15     # Подовження життя при "Погодитися" (+15 хв)
DOWNVOTE_REDUCE_MINUTES = 15    # Скорочення життя при "Не погодитися" (-15 хв)

# --- СЕРВЕР ---
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", "8080"))
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://laughing-person-recall-apps.trycloudflare.com")

# --- СТАТУСИ ТА ТИПИ ПОДІЙ ---
STATUSES = {
    "green": {
        "title": "Все спокійно",
        "color": "#22c55e",
        "pulse_class": "pulse-green",
        "icon": "fa-circle-check",
        "description": "Обстановка спокійна, перешкод немає"
    },
    "red": {
        "title": "Тривога",
        "color": "#ef4444",
        "pulse_class": "pulse-red",
        "icon": "fa-bell-exclamation",
        "description": "Тривога! Інцидент, ДТП, затор або небезпека"
    },
    "yellow": {
        "title": "Під питанням",
        "color": "#eab308",
        "pulse_class": "pulse-yellow",
        "icon": "fa-circle-question",
        "description": "Подія вимагає підтвердження"
    }
}
