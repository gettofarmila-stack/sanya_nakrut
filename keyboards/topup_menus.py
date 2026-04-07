from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def confim_payment():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Да, уверен', callback_data='confirm_payment'))
    return builder.as_markup()

def update_payment(payment_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Проверить оплату', callback_data=f'check_{payment_id}'))
    return builder.as_markup()