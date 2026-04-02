import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import my_token
from handlers import common

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

async def main():
    bot = Bot(token=my_token)
    dp = Dispatcher()
    
    dp.include_router(
        common.router
    )
    
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logging.info('Бот запущен')
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")