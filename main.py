# bot.py
import logging
import pytz
import datetime
import requests
import os
from telegram.ext import Updater, CommandHandler

# Включаем логгирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен Telegram бота и API-ключ OpenWeather из переменных окружения
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Город: (название для OpenWeather, часовой пояс)
cities = {
    "Ростов-на-Дону": ("Rostov-on-Don,ru", "Europe/Moscow"),
    "Абовян": ("Abovyan,am", "Asia/Yerevan"),
    "Дения": ("Denia,es", "Europe/Madrid")
}

# Получение времени и погоды по каждому городу
def get_time_and_weather():
    result = ""
    for display_name, (weather_city, tz) in cities.items():
        try:
            now = datetime.datetime.now(pytz.timezone(tz)).strftime("%H:%M")
            weather = get_weather(weather_city)
            result += f"🕒 {display_name}: {now}\n🌤️ {weather}\n\n"
        except Exception as e:
            logger.error(f"Ошибка для города {display_name}: {e}")
            result += f"🕒 {display_name}: {now}\n🌤️ Ошибка получения погоды\n\n"
    return result

# Получение погоды из OpenWeather
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url).json()
        if response.get("main"):
            temp = response["main"]["temp"]
            description = response["weather"][0]["description"]
            return f"{description.capitalize()}, {temp}°C"
        else:
            logger.error(f"Ошибка API для города {city}: {response.get('message', 'Неизвестная ошибка')}")
            return "Погода не найдена"
    except Exception as e:
        logger.error(f"Ошибка запроса погоды для {city}: {e}")
        return "Погода не найдена"

# Команда /start
def start(update, context):
    try:
        message = get_time_and_weather()
        update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# Отправка ежедневного сообщения
def daily_job(context):
    try:
        chat_id = context.job.context
        context.bot.send_message(chat_id=chat_id, text=get_time_and_weather())
    except Exception as e:
        logger.error(f"Ошибка в ежедневной задаче: {e}")

# Команда /daily
def set_daily_notification(update, context):
    try:
        chat_id = update.message.chat_id
        tz = pytz.timezone("Asia/Yerevan")
        now = datetime.datetime.now(tz)
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        delay = (target - now).total_seconds()
        if delay < 0:
            delay += 86400  # На следующий день
        context.job_queue.run_repeating(daily_job, interval=86400, first=delay, context=chat_id)
        update.message.reply_text("✅ Напоминание настроено на каждый день в 9:00 по ереванскому времени.")
    except Exception as e:
        logger.error(f"Ошибка в команде /daily: {e}")
        update.message.reply_text("Ошибка при настройке напоминания.")

# Основная функция
def main():
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # Добавляем обработчики команд
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("daily", set_daily_notification))

        # Запускаем бота
        updater.start_polling()
        logger.info("Бот запущен")
        updater.idle()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
