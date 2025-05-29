import os
import logging
from aiohttp import web
import aiohttp
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN", "7711881075:AAH9Yvz9vRTabNUcn7fk5asEX6RoL0Gy9_k")
ADMIN_ID = os.getenv("ADMIN_ID", "7586559527")
PORT = int(os.getenv("PORT", 8080))
ALLOWED_ORIGINS = [
    "https://project-tg-frontend-git-main-ermegors-projects.vercel.app",
    "http://localhost:3000"
]

async def send_log_to_telegram(message):
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": ADMIN_ID,
                "text": f"Лог (server.py): {message}",
                "parse_mode": "HTML"
            }
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки лога в Telegram: {error_text}")
                else:
                    logger.info("Лог успешно отправлен в Telegram")
        except Exception as e:
            logger.error(f"Ошибка отправки лога в Telegram: {str(e)}")

async def cors_middleware(app, handler):
    async def middleware(request):
        origin = request.headers.get('Origin', '')
        logger.info(f"[Middleware] Origin: {origin}, Method: {request.method}")
        await send_log_to_telegram(f"[Middleware] Origin: {origin}, Method: {request.method}")
        response = await handler(request)
        if origin in ALLOWED_ORIGINS or True:  # Временно разрешаем все для теста
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    return middleware

async def handle_root(request):
    logger.info("Получен запрос на корневой маршрут")
    await send_log_to_telegram("Получен запрос на /")
    return web.Response(text="Server is running")

async def handle_test(request):
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": ADMIN_ID,
                "text": "Тестовое сообщение от сервера server.py",
                "parse_mode": "HTML"
            }
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return web.Response(text=f"Ошибка: {error_text}")
                return web.Response(text="Тестовое сообщение отправлено")
        except Exception as e:
            return web.Response(text=f"Ошибка: {str(e)}")

async def handle_submit(request):
    logger.info(f"Получен запрос: {request.method} /submit")
    await send_log_to_telegram(f"Получен запрос: {request.method} /submit")
    
    headers_str = ", ".join([f"{key}: {value}" for key, value in request.headers.items()])
    logger.info(f"Заголовки запроса: {headers_str}")
    await send_log_to_telegram(f"Заголовки запроса: {headers_str}")
    
    try:
        raw_data = await request.read()
        data = json.loads(raw_data.decode('utf-8'))  # Явно декодируем какs UTF-8
        logger.info(f"Тело запроса: {data}")
        await send_log_to_telegram(f"Тело запроса: {json.dumps(data, ensure_ascii=False)}")
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {str(e)}")
        await send_log_to_telegram(f"Ошибка декодирования JSON: {str(e)}")
        return web.Response(text="Ошибка: Неверный формат данных", status=400)

    name = data.get('name', 'Не указано')
    message = data.get('message', 'Не указано')
    
    msg = f"<b>Новая заявка (через сервер)</b>\nИмя: {name}\nСообщение: {message}"
    logger.info(f"Отправляем сообщение администратору {ADMIN_ID}: {msg}")
    await send_log_to_telegram(f"Отправляем сообщение администратору: {msg}")
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": ADMIN_ID,
                "text": msg,
                "parse_mode": "HTML"
            }
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки сообщения: {error_text}")
                    await send_log_to_telegram(f"Ошибка отправки сообщения: {error_text}")
                    return web.Response(text=f"Ошибка отправки: {error_text}", status=500)
                logger.info("Сообщение успешно отправлено")
                await send_log_to_telegram("Сообщение успешно отправлено")
                return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await send_log_to_telegram(f"Ошибка: {str(e)}")
            return web.Response(text=f"Ошибка: {str(e)}", status=500)

app = web.Application(middlewares=[cors_middleware])
app.router.add_get('/', handle_root)
app.router.add_get('/test', handle_test)
app.router.add_post('/submit', handle_submit)

if __name__ == "__main__":
    logger.info(f"Запускаем сервер на 0.0.0.0:{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)