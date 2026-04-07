import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from config import my_token
from handlers import common, order, trades, topup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

router = Router()
@router.error()
async def error_handler(event: types.ErrorEvent):
    logging.error(f"ОШИБКА: {event.exception}")
    
async def main():
    bot = Bot(token=my_token)
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_routers(common.router, order.router, trades.router, topup.router)

    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logging.info('Бот запущен')
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")