
import asyncio
from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from logic.order_logic import get_my_old_orders, get_my_order, get_my_orders, inline_keyboards_old_order, inline_keyboards_order, update_order



router = Router()

@router.callback_query(F.data.startswith('selectold_'))
async def select_old_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split('_')[1])
    service_id = int(callback.data.split('_')[2])
    orders = await asyncio.to_thread(get_my_order, order_id, service_id)
    keyboard = await asyncio.to_thread(inline_keyboards_old_order, callback.from_user.id)
    await callback.message.edit_text(orders, reply_markup=keyboard)

@router.callback_query(F.data.startswith('go_to_old_orders'))
async def go_to_old_orders_inline(callback: types.CallbackQuery):
    orders = await asyncio.to_thread(get_my_old_orders, callback.from_user.id)
    await callback.message.edit_text(f'Ваши заказы:', reply_markup=orders)

@router.callback_query(F.data.startswith('go_my_orders'))
async def go_my_orders(callback: types.CallbackQuery):
    orders = await asyncio.to_thread(get_my_orders, callback.from_user.id)
    await callback.message.edit_text(f'Ваши заказы: ', reply_markup=orders)

@router.callback_query(F.data.startswith('select_'))
async def select_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split('_')[1])
    service_id = int(callback.data.split('_')[2])
    orders = await asyncio.to_thread(get_my_order, order_id, service_id)
    keyboard = await asyncio.to_thread(inline_keyboards_order, callback.from_user.id, order_id, service_id)
    await callback.message.edit_text(orders, reply_markup=keyboard)

@router.callback_query(F.data.startswith('update_'))
async def update_order_callback(callback: types.CallbackQuery):
    data = callback.data.split('_')
    order_id = int(data[1])
    service_id = int(data[2])
    update_status = await update_order(order_id)
    orders = await asyncio.to_thread(get_my_order, order_id, service_id)
    keyboard = await asyncio.to_thread(inline_keyboards_order, callback.from_user.id, order_id, service_id)
    try:
        await callback.message.edit_text(orders, reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" in e.message:
            pass
        else:
            raise e
    await callback.answer(update_status)

#@router.callback_query(F.data.startswith('refill_'))
#async def refill_order_callback(callback: types.CallbackQuery):
#    order_id = int(callback.data.split('_')[1])
#    service_id = int(callback.data.split('_')[2])
#    orders = await asyncio.to_thread(get_my_order, order_id, service_id)
#    refill_status = await refill_order(order_id)
#    keyboard = await asyncio.to_thread(inline_keyboards_order, callback.from_user.id, order_id, service_id)
#    try:
#        await callback.message.edit_text(orders, reply_markup=keyboard)
#    except TelegramBadRequest as e:
#        if 'message is not modified' in e.message:
#            pass
#        else:
#            raise e
#        await callback.answer(refill_status)