import asyncio
from aiogram import Bot
import config

async def check():
    bot = Bot(token=config.BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"Bot: @{me.username} (id={me.id})")
        
        chat = await bot.get_chat(config.TARGET_CHANNEL)
        print(f"Channel: {chat.title} (id={chat.id})")
        
        member = await bot.get_chat_member(config.TARGET_CHANNEL, me.id)
        print(f"Bot role in channel: {member.status}")
        can_post = getattr(member, "can_post_messages", "N/A")
        print(f"Can post messages: {can_post}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

asyncio.run(check())
