
import aiohttp
import logging
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.engine import Session, AsyncSession
from database.models import Order, Products
from sqlalchemy import select
from config import smm_key, smm_link
from datetime import datetime

def get_my_orders(uid):
    builder = InlineKeyboardBuilder()
    with Session() as session:
        orders = session.execute(select(Order).where(Order.owner_id == uid, Order.status.not_in(["Completed", "Canceled"]))).scalars().all()
        if not orders:
            return None
        serv_ids = list(set(order.service_id for order in orders))
        services_query = session.execute(select(Products).where(Products.service_id.in_(serv_ids))).scalars().all()
        services_dict = {s.service_id: s for s in services_query}
        for order in orders:
            serv = services_dict.get(order.service_id)
            name = serv.name if serv else f"Услуга #{order.service_id}"
            builder.row(types.InlineKeyboardButton(text=f"{name} (ID: {order.order_id})", callback_data=f'select_{order.order_id}_{order.service_id}'))
        return builder.as_markup()
    
def get_my_old_orders(uid):
    builder = InlineKeyboardBuilder()
    with Session() as session:
        orders = session.execute(select(Order).where(Order.owner_id == uid, Order.status.in_(['Completed', 'Canceled']))).scalars().all()
        if not orders:
            return None
        serv_ids = list(set(order.service_id for order in orders))
        services_query = session.execute(select(Products).where(Products.service_id.in_(serv_ids))).scalars().all()
        services_dict = {s.service_id: s for s in services_query}
        for order in orders:
            serv = services_dict.get(order.service_id)
            name = serv.name if serv else f'Услуга #{order.service_id}'
            builder.row(types.InlineKeyboardButton(text=f"{name} (ID: {order.order_id})", callback_data=f'selectold_{order.order_id}_{order.service_id}'))
        return builder.as_markup()
    
async def update_order(order_id):
    async with AsyncSession() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        current_time = datetime.now()
        if (current_time - order.update_cooldown).total_seconds() < 120:
            return('Не удалось обновить! Кд на запрос 2 минуты')
        async with aiohttp.ClientSession() as csession:
            url = f'{smm_link}?action=status&order={order_id}&key={smm_key}'
            async with csession.get(url) as response:
                data = await response.json()
                order.remains = int(data['remains'])
                order.status = data['status']
                order.update_cooldown = current_time
                await session.commit()
                return('Обновлено')

async def refill_order(order_id):
    async with aiohttp.ClientSession() as session:
        url = f'{smm_link}?action=refill&order={order_id}&key={smm_key}'
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return 'Сервер API временно недоступен'         
                data = await response.json()
                refill_id = data.get('refill')
                if 'error' in data:
                    return f"Ошибка: {data['error']}"
                if str(refill_id) == str(order_id):
                    return '✅ Рефилл успешно запущен!'
                logging.warning(f"Неожиданный ответ рефилла для {order_id}: {data}")
                return '⚠️ Не удалось запустить рефилл'
        except Exception as e:
            logging.error(f"Ошибка при запросе рефилла: {e}")
            return '❌ Ошибка сети или API' 

#async def cancel_order(order_id):
#    async with aiohttp.ClientSession() as session:
#        url = f'{smm_link}?action=cancel&order={order_id}&key={smm_key}'
#        async with session.get(url) as response:
#            data = await response.json()
#            if data['ok'] == 'true':
#                return('Успешно отменено')
#            else:
#                return('Что-то пошло не так')

def inline_keyboards_order(uid, order_id, service_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Обновить статус', callback_data=f'update_{order_id}_{service_id}'))
#    builder.row(types.InlineKeyboardButton(text='Рефилл', callback_data=f'refill_{order_id}_{service_id}'))
#    builder.row(types.InlineKeyboardButton(text='Отменить заказ', callback_data=f'cancel_{order_id}')
    builder.row(types.InlineKeyboardButton(text='Назад', callback_data=f'go_my_orders'))
    return builder.as_markup()

def inline_keyboards_old_order(uid, order_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Удалить из истории', callback_data=f'removeoldorder_{order_id}'))
    builder.row(types.InlineKeyboardButton(text='Назад', callback_data=f'go_to_old_orders'))
    return builder.as_markup()

async def remove_old_order(order_id):
    async with AsyncSession() as session:
        order_beta = await session.execute(select(Order).where(Order.order_id == order_id))
        order = order_beta.scalar_one_or_none()
        await session.delete(order)
        await session.commit()
        return('Успешно удалено!')

def get_my_order(order_id, service_id):
    with Session() as session:
        order = session.execute(select(Order).where(Order.order_id == order_id)).scalar_one_or_none()
        service = session.execute(select(Products).where(Products.service_id == service_id)).scalar_one_or_none()
        return(f'''
            {service.name}
Ваш заказ под айди: {order.order_id}               
Сумма заказа: {order.order_sum}
Осталось к получению: {order.remains}
Статус заказа: {order.status}
Если заказ отменили сразу после, напишите в поддержку и мы вернём вам баланс, иногда бывают отмены из-за тех.неполадок...
               ''')