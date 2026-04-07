from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder



def remove_confirmation(order_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Удалить', callback_data=f'removeold_{order_id}'))
    return builder.as_markup()