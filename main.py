from itertools import count
import pytz
import subprocess
import sys
import sys
import importlib.util

# Загружаем ваш файл как модуль
# Строка 9:
spec = importlib.util.spec_from_file_location("weather", "ParsTemp.py")
weather_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather_module)
try:
    from bs4 import BeautifulSoup as BS
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup as BS
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ChatMemberHandler, filters, ConversationHandler, CallbackQueryHandler, CallbackContext, ContextTypes
)
from telegram.constants import ChatMemberStatus, ParseMode
import requests
import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import ParsTemp



BANNED_USERS = []  # username без @ в нижнем регистре
BANNED_USERNAMES_WITH_AT = [f"@{user}" for user in BANNED_USERS]
# ParsTemp.parsing_temp(ParsTemp.times, ParsTemp.tempes, ParsTemp.all_dates)

BOT_TOKEN = "8416702729:AAFNNb2xMA-vhHHzohiMZv080zkCZRzRLmA"
TIMEZONE = pytz.timezone('Europe/Moscow')
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Приветствие! еще раз?)", callback_data="Hi"),
            InlineKeyboardButton("Показать температуру на неделю?", callback_data="parsing_Temp")
        ],
        [
            InlineKeyboardButton("Сообщить об ошибке", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def hello_message(update: Update, context):
    keyboard = get_main_keyboard()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {update.effective_user.first_name}!\n\n"
            "Я бот для показа погоды в СПб на целую неделю!!!\n\n"
            "📌 *Такие команды у меня есть:*",
        reply_markup=keyboard,
        parse_mode="markdown"
    )




async def parsing_telega_message(update: Update, context):
    keyboard = get_main_keyboard()

    importlib.reload(weather_module)

    # Теперь используем ваши функции
    weather = weather_module.parsing_temp(
        weather_module.times,
        weather_module.tempes,
        weather_module.all_dates,
        weather_module.clouds
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🌤 *Прогноз погоды:*\n\n{weather}",
        parse_mode="MarkdownV2"
    )






async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет я бот созданный для того,\n чтобы ты не замерзал и не потел в холодное и теплое время года в СПб\nУ меня есть такие функции: "
    )


async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == "Hi":
        await hello_message(update, context)
    elif data == "parsing_Temp":
        await parsing_telega_message(update, context)


async def is_admin(update: Update, user_id: int) -> bool:
    try:
        chat_member = await update.effective_chat.get_member(user_id)
        return chat_member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except:
        return False



async def send_daily_message(app: Application):
    keyboard = get_main_keyboard()
    weather = parsing_temp_day(ParsTemp.times,ParsTemp.tempes,ParsTemp.all_dates,ParsTemp.clouds)
    await app.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Доброе утро программисты\n\n{weather}",
        parse_mode="MarkdownV2",
    )

async def on_startup():
    scheduler.add_job(
        send_daily_message,
        CronTrigger(hour=6, minute=0,timezone = timezone('Europe/Moscow')),  # Уже 6:00 по TIMEZONE
        id="daily_message"
    )
    scheduler.start()
    logging.info("Планировщик запущен. Сообщение будет приходить каждый день в 6:00")

# Остановка планировщика при завершении
async def on_shutdown():
    scheduler.shutdown()
    await bot.session.close()


async def ban_ebanatov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Работаем только в группах
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    msg_text = update.message.text.lower()
    user_username = user.username.lower() if user.username else ""
    username_with_at = f"@{user.username}" if user.username else ""

    # СПИСОК ЗАБАНЕННЫХ (вынесите в начало файла)


    # ПРОВЕРКА НА БАН В САМОМ НАЧАЛЕ!
    if user_username in BANNED_USERS:
        await update.message.delete()
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🚫 {user.first_name} сорри, не сегодня"
        )
        return

    if "калл" in msg_text:
        # Удаляем сообщение
        await update.message.delete()

        # Получаем администраторов чата (вместо всех участников)
        # Получить ВСЕХ участников чата через API невозможно (ограничение Telegram)
        members_list = []

        try:
            # Получаем администраторов
            admins = await context.bot.get_chat_administrators(chat.id)
            for admin in admins:
                if admin.user.id != context.bot.id:
                    if admin.user.username:
                        members_list.append(f"@{admin.user.username}")
                    else:
                        members_list.append(f'<a href="tg://user?id={admin.user.id}">{admin.user.first_name}</a>')

            # Также добавляем того, кто написал "калл"
            if user.id not in [admin.user.id for admin in admins]:
                if user.username:
                    members_list.append(f"@{user.username}")
                else:
                    members_list.append(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')

        except Exception as e:
            print(f"Ошибка при получении списка участников: {e}")
            # Если не удалось получить список, отправляем простое сообщение
            mention_text = f"📢 {user.first_name} нарушил правила!"
            await context.bot.send_message(
                chat_id=chat.id,
                text=mention_text
            )
            return

        if members_list:
            mention_text = f"📢 {user.first_name} вызвал всех:\n" + "\n".join(members_list[:30])
        else:
            mention_text = f"📢 {user.first_name} нарушил правила!"

        await context.bot.send_message(
            chat_id=chat.id,
            text=mention_text,
            parse_mode="HTML"
        )
    # if await is_admin(update, user_id):
    #     return













async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("Pogoda", parsing_telega_message))

    app.add_handler(CallbackQueryHandler(button_callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ban_ebanatov))

    # Обработчик добавления бота в чат
    app.add_handler(ChatMemberHandler(hello_message, ChatMemberHandler.MY_CHAT_MEMBER))

    scheduler.add_job(
        lambda: send_daily_message(app),  # Передаём app в функцию
        CronTrigger(hour=6, minute=0),
        id="daily_message"
    )

    print("🤖 Бот запущен...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # Держим бота запущенным
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    finally:
        await app.stop()


def main():
    """Главная функция"""
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()




