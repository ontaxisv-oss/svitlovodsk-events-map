import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

SURGE_MAP_URL = "https://svitlovodsk-map.surge.sh"
BOT_USERNAME = "kr_olive_bot"

def get_map_inline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗺 Відкрити Карту Подій", url=SURGE_MAP_URL)
    ]])

def get_channel_pinned_kb():
    """Кнопки для закріпленого повідомлення в каналі — Mini App + посилання на бот"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🗺 Карта Подій (Mini App)",
                web_app=WebAppInfo(url=SURGE_MAP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Повідомити про подію",
                url=f"https://t.me/{BOT_USERNAME}"
            )
        ]
    ])

def get_event_vote_kb(event_id, upvotes=1, downvotes=0):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"👍 Погодитися ({upvotes})", callback_data=f"vote_up_{event_id}"),
            InlineKeyboardButton(text=f"👎 Не погодитися ({downvotes})", callback_data=f"vote_down_{event_id}")
        ],
        [InlineKeyboardButton(text="🗺 Дивитись на карті", url=SURGE_MAP_URL)]
    ])

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺 Відкрити Інтерактивну Карту")],
            [KeyboardButton(text="📋 Список активних подій")],
            [
                KeyboardButton(text="📍 Події поруч зі мною", request_location=True),
                KeyboardButton(text="ℹ️ Інструкція та правила")
            ]
        ],
        resize_keyboard=True
    )

@dp.message(F.chat.type == "private", F.text == "🗺 Відкрити Інтерактивну Карту")
async def cmd_open_map_btn(message: types.Message):
    text = (
        f"🗺 <b>Інтерактивна Карта Подій м. {config.CITY_NAME}</b>\n\n"
        f"Натисніть на кнопку нижче, щоб відкрити графічну карту з вулицями, маркерами та орієнтирами у браузері вашого телефону:"
    )
    kb = get_map_inline_kb()
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(F.chat.type == "private", CommandStart())
@dp.message(F.chat.type == "private", Command("map"))
@dp.message(F.chat.type == "private", F.text == "📋 Список активних подій")
async def cmd_start(message: types.Message):
    active_events = database.get_active_events(4)
    status_icons = {"green": "🟢", "red": "🔴", "yellow": "🟡"}
    
    if not active_events:
        welcome = (
            f"🌍 <b>Карта Подій міста {config.CITY_NAME}</b>\n"
            f"📡 Джерело: t.me/{config.SOURCE_CHANNEL}\n\n"
            f"🟢 <b>На даний момент у Світловодську все спокійно, активних інцидентів немає!</b>\n\n"
            f"Ви можете відправити текстове повідомлення у цей чат, щоб повідомити про ситуацію на дорогах."
        )
        await message.answer(welcome, parse_mode="HTML", reply_markup=get_main_keyboard())
        return

    await message.answer(
        f"🚨 <b>Оперативна сводка подій у м. {config.CITY_NAME}:</b>\n"
        f"<i>Знайдено активних подій: {len(active_events)}</i>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

    for ev in active_events[:5]:
        icon = status_icons.get(ev.get('status'), '⚪️')
        rem = ev.get('remaining_minutes', 240)
        ev_id = ev.get('id')
        
        card_text = (
            f"{icon} <b>{ev.get('title', 'Подія')}</b>\n"
            f"💬 <b>Повідомлення:</b> {ev.get('description', '')}\n"
            f"⏱ <b>Дійсне ще:</b> {rem} хв\n"
            f"👤 Автор: {ev.get('author_name', 'Користувач')}"
        )
        kb = get_event_vote_kb(ev_id, ev.get('upvotes', 1), ev.get('downvotes', 0))
        await message.answer(card_text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith("vote_up_"))
async def handle_vote_up(callback: types.CallbackQuery):
    event_id = callback.data.replace("vote_up_", "")
    user_id = callback.from_user.id
    
    updated = database.vote_event(event_id, user_id, "up")
    if updated:
        kb = get_event_vote_kb(event_id, updated.get('upvotes', 1), updated.get('downvotes', 0))
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
        await callback.answer("👍 Ваш голос враховано! Час життя події подовжено на +15 хв.")
    else:
        await callback.answer("⚠️ Ви вже голосували за цю подію або термін її дії закінчився.")

@dp.callback_query(F.data.startswith("vote_down_"))
async def handle_vote_down(callback: types.CallbackQuery):
    event_id = callback.data.replace("vote_down_", "")
    user_id = callback.from_user.id
    
    updated = database.vote_event(event_id, user_id, "down")
    if updated:
        kb = get_event_vote_kb(event_id, updated.get('upvotes', 1), updated.get('downvotes', 0))
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
        await callback.answer("👎 Ваш голос враховано! Час життя події скорочено на -15 хв.")
    else:
        await callback.answer("⚠️ Ви вже голосували за цю подію або термін її дії закінчився.")

@dp.message(F.text == "ℹ️ Інструкція та правила")
async def cmd_rules(message: types.Message):
    rules_text = (
        f"📖 <b>Інструкція з використання «Карта подій»:</b>\n\n"
        f"<b>1. Позначення подій:</b>\n"
        f"• 🟢 Зелений – Все спокійно.\n"
        f"• 🔴 Червоний – Щось трапилося (ДТП, затор, перешкода).\n"
        f"• 🟡 Жовтий – Під питанням / на перевірці.\n\n"
        f"<b>2. Голосування:</b>\n"
        f"• <b>👍 Погодитися (+15 хв)</b> — підтвердити та подовжити актуальність.\n"
        f"• <b>👎 Не погодитися (-15 хв)</b> — спростувати та скоротити час показу.\n\n"
        f"<b>3. Автоматичне прибрання:</b>\n"
        f"• Усі події автоматично зникають через 15 хвилин.\n\n"
        f"📡 Оперативний канал: @{config.SOURCE_CHANNEL}"
    )
    await message.answer(rules_text, parse_mode="HTML")

@dp.message(F.chat.type == "private", F.location)
async def handle_user_location(message: types.Message):
    active_events = database.get_active_events()
    if not active_events:
        await message.answer("🟢 На даний момент у Світловодську все спокійно, активних подій немає!")
        return

    status_icons = {"green": "🟢", "red": "🔴", "yellow": "🟡"}
    await message.answer("📍 <b>Найближчі події у Світловодську:</b>", parse_mode="HTML")
    
    for ev in active_events[:5]:
        icon = status_icons.get(ev.get('status'), '⚪️')
        rem_min = ev.get("remaining_minutes", 240)
        card_text = (
            f"{icon} <b>{ev.get('title')}</b>\n"
            f"💬 {ev.get('description')}\n"
            f"⏱ Дійсне ще: <b>{rem_min} хв</b>"
        )
        kb = get_event_vote_kb(ev.get('id'), ev.get('upvotes', 1), ev.get('downvotes', 0))
        await message.answer(card_text, parse_mode="HTML", reply_markup=kb)

@dp.message(F.chat.type == "private", F.text & ~F.text.startswith("/"))
async def handle_incoming_text_or_forward(message: types.Message):
    if message.text in ["ℹ️ Інструкція та правила", "📋 Список активних подій"]:
        return

    import parser
    text = message.text.strip()
    status = parser.detect_status(text)
    loc_name, lat, lng = parser.detect_location(text)
    
    author_name = message.from_user.first_name if message.from_user else "Користувач"
    title = f"{loc_name} ({config.STATUSES[status]['title']})"

    # 1. Зберігаємо в базу та ставимо метку на карті
    new_event = database.add_event(
        status=status,
        title=title,
        description=text,
        lat=lat,
        lng=lng,
        author_name=author_name,
        author_id=message.from_user.id if message.from_user else 0,
        custom_ttl_hours=config.DEFAULT_EVENT_TTL_HOURS
    )

    status_icon = "🟢" if status == "green" else ("🔴" if status == "red" else "🟡")
    event_id = new_event.get('id')

    reply_text = (
        f"✅ <b>Метку поставлено на карті!</b>\n\n"
        f"Статус: {status_icon} <b>{config.STATUSES[status]['title']}</b>\n"
        f"Локація: <b>{loc_name}</b>\n\n"
        f"⏱ <i>Метка зникне через 15 хвилин</i>"
    )

    kb = get_event_vote_kb(event_id, 1, 0)
    await message.answer(reply_text, parse_mode="HTML", reply_markup=kb)

@dp.channel_post()
async def handle_channel_post(message: types.Message):
    """Слухає нові пости у каналі @kr_probki та автоматично ставить метку на карту"""
    text = message.text or message.caption or ""
    text = text.strip()
    if not text or len(text) < 3:
        return

    import parser as p
    status = p.detect_status(text)
    loc_name, lat, lng = p.detect_location(text)
    title = f"{loc_name} ({config.STATUSES[status]['title']})"
    status_icon = "🟢" if status == "green" else ("🔴" if status == "red" else "🟡")

    new_ev = database.add_event(
        status=status,
        title=title,
        description=text,
        lat=lat,
        lng=lng,
        author_name=f"@kr_probki",
        custom_ttl_hours=config.DEFAULT_EVENT_TTL_HOURS
    )
    print(f"📌 [kr_probki] {status_icon} Нова метка: {title}")

    # Видаляємо пост з каналу після обробки
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        print(f"🗑 Пост видалено з каналу (msg_id={message.message_id})")
    except Exception as e:
        print(f"⚠️ Не вдалося видалити пост з каналу: {e}")

async def post_channel_pinned_message():
    """Публікує/оновлює закріплене повідомлення у каналі @kr_probki"""
    text = (
        f"📡 <b>Карта Подій м. Світловодськ</b>\n\n"
        f"Тут відображаються актуальні події на дорогах та у місті в режимі реального часу.\n\n"
        f"⏱ Метки живуть <b>15 хвилин</b>, потім зникають автоматично.\n"
        f"👍 Голосуй щоб продовжити або скасувати подію.\n\n"
        f"✏️ Щоб повідомити про подію — пиши боту @{BOT_USERNAME}"
    )
    try:
        msg = await bot.send_message(
            chat_id=config.TARGET_CHANNEL,
            text=text,
            parse_mode="HTML",
            reply_markup=get_channel_pinned_kb()
        )
        await bot.pin_chat_message(
            chat_id=config.TARGET_CHANNEL,
            message_id=msg.message_id,
            disable_notification=True
        )
        print(f"📌 Закріплене повідомлення опубліковано в {config.TARGET_CHANNEL}")
    except Exception as e:
        print(f"⚠️ Не вдалося опублікувати закріплене повідомлення: {e}")

@dp.message(F.chat.type == "private", Command("pin"))
async def cmd_pin(message: types.Message):
    """Адмін-команда: /pin — публікує закріплене повідомлення в канал"""
    await post_channel_pinned_message()
    await message.answer("✅ Закріплене повідомлення опубліковано у каналі!")

async def start_bot():
    print(f"🤖 Бот Карта Подій Світловодськ запущен у нативному режимі!")
    await post_channel_pinned_message()
    await dp.start_polling(bot)
