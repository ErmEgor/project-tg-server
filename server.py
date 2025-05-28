import asyncio
import json
import os
import logging
from aiohttp import web
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN", "7711881075:AAH9Yvz9vRTabNUcn7fk5asEX6RoL0Gy9_k")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7586559527"))
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Функция для отправки логов в Telegram
async def send_log_to_telegram(message):
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"<b>Лог (server.py):</b>\n{message}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка отправки лога в Telegram: {e}")

# Обработчик POST-запроса
async def handle_submit(request):
    logger.info(f"Получен запрос: {request.method} {request.path}")
    await send_log_to_telegram(f"Получен запрос: {request.method} {request.path}")
    logger.info(f"Заголовки запроса: {request.headers}")
    await send_log_to_telegram(f"Заголовки запроса: {request.headers}")
    try:
        data = await request.json()
        logger.info(f"Тело запроса: {data}")
        await send_log_to_telegram(f"Тело запроса: {data}")
        name = data.get('name', 'Не указано')
        msg_text = data.get('message', 'Не указано')
        text = f"<b>Новая заявка (через сервер)</b>\nИмя: {name}\nСообщение: {msg_text}"
        logger.info(f"Отправляем сообщение администратору {ADMIN_ID}: {text}")
        await send_log_to_telegram(f"Отправляем заявку администратору: {text}")
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode=ParseMode.HTML)
        logger.info("Сообщение успешно отправлено")
        await send_log_to_telegram("Сообщение успешно отправлено")
        return web.json_response({'status': 'success'})
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка JSON в POST-запросе: {e}")
        await send_log_to_telegram(f"Ошибка JSON в POST-запросе: {e}")
        return web.json_response({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка обработки POST-запроса: {e}")
        await send_log_to_telegram(f"Ошибка обработки POST-запроса: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# Обработчик OPTIONS-запроса (preflight)
async def handle_options(request):
    origin = request.headers.get('Origin', '')
    logger.info(f"[OPTIONS] Origin: {origin}")
    await send_log_to_telegram(f"[OPTIONS] Origin: {origin}")
    response = web.Response(status=200)
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Middleware для CORS
ALLOWED_ORIGINS = {
    'https://project-tg-frontend-git-main-ermegors-projects.vercel.app',
    'https://project-tg-frontend-sigma.vercel.app',
    'https://project-tg-frontend-iq1dv9sx9-ermegors-projects.vercel.app',
}

async def cors_middleware(app, handler):
    async def middleware(request):
        origin = request.headers.get('Origin', '')
        logger.info(f"[Middleware] Origin: {origin}, Method: {request.method}")
        await send_log_to_telegram(f"[Middleware] Origin: {origin}, Method: {request.method}")
        response = await handler(request)
        if origin in ALLOWED_ORIGINS or 'vercel.app' in origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    return middleware

# --- HTTP-маршруты для отладки ---
async def handle_root(request):
    logger.info("Получен запрос на корневой маршрут")
    await send_log_to_telegram("Получен запрос на /")
    return web.Response(text="Server is running")

async def handle_logs(request):
    logger.info("Получен запрос на просмотр логов")
    await send_log_to_telegram("Запрос на просмотр логов /logs")
    try:
        with open('app.log', 'r') as f:
            logs = f.read()
        return web.Response(text=logs)
    except FileNotFoundError:
        return web.Response(text="Логи не найдены")

async def handle_test(request):
    logger.info("Получен тестовый запрос /test")
    await send_log_to_telegram("Тестовый запрос /test")
    try:
        await bot.send_message(chat_id=ADMIN_ID, text="Тестовое сообщение от сервера server.py")
        return web.Response(text="Тестовое сообщение отправлено в Telegram")
    except Exception as e:
        logger.error(f"Ошибка тестового сообщения: {e}")
        await send_log_to_telegram(f"Ошибка тестового сообщения: {e}")
        return web.Response(text=f"Ошибка: {e}")

# Настройка приложения
app = web.Application()
app.middlewares.append(cors_middleware)
app.add_routes([
    web.post('/submit', handle_submit),
    web.options('/submit', handle_options),
    web.get('/', handle_root),
    web.get('/logs', handle_logs),
    web.get('/test', handle_test)
])

# Запуск сервера
async def main():
    logger.info(f"Запускаем сервер на {WEBAPP_HOST}:{WEBAPP_PORT}")
    await send_log_to_telegram(f"Запускаем сервер на {WEBAPP_HOST}:{WEBAPP_PORT}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    logger.info(f"Сервер запущен на {WEBAPP_HOST}:{WEBAPP_PORT}")
    await send_log_to_telegram(f"Сервер запущен на {WEBAPP_HOST}:{WEBAPP_PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())