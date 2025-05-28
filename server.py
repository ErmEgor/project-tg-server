import asyncio
import json
import os
from aiohttp import web
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN") or "7711881075:AAH9Yvz9vRTabNUcn7fk5asEX6RoL0Gy9_k"  # Резервный токен
ADMIN_ID = int(os.getenv("ADMIN_ID") or "7586559527")  # Резервный ID
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Обработчик POST-запроса
async def handle_submit(request):
    print(f"Получен запрос: {request.method} {request.path}")
    print(f"Заголовки запроса: {request.headers}")
    try:
        data = await request.json()
        print(f"Тело запроса (сырые данные): {data}")
        name = data.get('name', 'Не указано')
        msg_text = data.get('message', 'Не указано')
        text = f"<b>Новая заявка (через сервер)</b>\nИмя: {name}\nСообщение: {msg_text}"
        print(f"Отправляем сообщение администратору {ADMIN_ID}: {text}")
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode=ParseMode.HTML)
        print("Сообщение успешно отправлено")
        return web.json_response({'status': 'success'})
    except json.JSONDecodeError as e:
        print(f"Ошибка JSON в POST-запросе: {e}")
        return web.json_response({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Ошибка обработки POST-запроса: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# Обработчик OPTIONS-запроса (preflight)
async def handle_options(request):
    origin = request.headers.get('Origin', '')
    print(f"[OPTIONS] Origin: {origin}")
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
        print(f"[Middleware] Origin: {origin}, Method: {request.method}")
        response = await handler(request)
        if origin in ALLOWED_ORIGINS or 'vercel.app' in origin:  # Разрешаем все поддомены vercel.app для отладки
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    return middleware

# Настройка приложения
app = web.Application()
app.middlewares.append(cors_middleware)
app.add_routes([
    web.post('/submit', handle_submit),
    web.options('/submit', handle_options)
])

# Запуск сервера
async def main():
    print(f"Запускаем сервер на {WEBAPP_HOST}:{WEBAPP_PORT}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    print(f"Сервер запущен на {WEBAPP_HOST}:{WEBAPP_PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())