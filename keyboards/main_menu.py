from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text='Товары'))
    builder.row(types.KeyboardButton(text='Мои заказы'), types.KeyboardButton(text='Профиль'))
    return builder.as_markup(resize_keyboard=True)

def profile_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text='Статистика'), types.KeyboardButton(text='Пополнение'))
    builder.row(types.KeyboardButton(text='Реферальная система'))
    builder.row(types.KeyboardButton(text='Главное меню'))
    return builder.as_markup(resize_keyboard=True)

def orders_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text='Текущие заказы'), types.KeyboardButton(text='История заказов'))
    builder.row(types.KeyboardButton(text='Главное меню'))
    return builder.as_markup(resize_keyboard=True)