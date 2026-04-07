import asyncio
import logging
from aiogram.filters.command import CommandStart, CommandObject
from aiogram import Router, F, types
from logic.user_logic import registration, is_user, get_my_stats
from keyboards.main_menu import main_menu_kb, profile_kb, orders_kb
from logic.trade_logic import category_render
from logic.order_logic import get_my_orders, get_my_old_orders
from aiogram.fsm.state import StatesGroup, State



class OrderProcess(StatesGroup):
    waiting_for_link = State()     #  Ссылка
    waiting_for_count = State()    # Количество
router = Router()

@router.message(CommandStart())
@router.message(F.text == 'Главное меню')
async def cmd_start(message: types.Message, command: CommandObject=None):
    args = command.args if command else None
    user_id = message.from_user.id
    if not is_user(user_id):
        ref_id = None
        if args and args.isdigit() and int(args) != user_id:
            ref_id = int(args)
            try:
                await message.bot.send_message(ref_id, '🤝 По вашей реферальной ссылке зашли!')
            except Exception:
                logging.error('Что-то пошло не так при регистрации')
        registrate = await asyncio.to_thread(registration, message.from_user.first_name, message.from_user.username, user_id, args)
        await message.answer(f'{registrate} Вы зарегестрировались по рефералочке')
    await message.answer(f'Привет! У нас ты можешь заказать накрутку по самым низким ценам.\nВыбери раздел:', reply_markup=main_menu_kb())

@router.message(F.text == 'Профиль')
async def profile_menu_handler(message: types.Message):
    await message.answer(f'Выбери, что хочешь посмотреть!', reply_markup=profile_kb())

@router.message(F.text == 'Мои заказы')
async def order_menu_hand(message: types.Message):
    orders = await asyncio.to_thread(orders_kb)
    await message.answer(f'Выбери, что хочешь посмотреть:', reply_markup=orders)

@router.message(F.text == 'Текущие заказы')
async def now_orders_hand(message: types.Message):
    orders = await asyncio.to_thread(get_my_orders, message.from_user.id)
    if orders:
        await message.answer(f'Ваши заказы: ', reply_markup=orders)
    else: 
        await message.answer(f'У вас ещё нет заказов!', reply_markup=orders)

@router.message(F.text == 'История заказов')
async def old_orders_hand(message: types.Message):
    orders = await asyncio.to_thread(get_my_old_orders, message.from_user.id)
    if orders:
        await message.answer(f'Ваши заказы: ', reply_markup=orders)
    else: 
        await message.answer(f'У вас ещё нет заказов!', reply_markup=orders)

@router.message(F.text == 'Реферальная система')
async def ref_system_handler(message: types.Message):
    bot_info = await message.bot.get_me()
    await message.answer(f'Приглашая друга, вы получаете 1% с каждого его пополнения!\nВаша реферальная ссылка:\nhttps://t.me/{bot_info.username}?start={message.from_user.id}')

@router.message(F.text == 'Товары')
async def products_one_menu_open(message: types.Message):
    categories = await asyncio.to_thread(category_render, page=0)
    await message.answer('Выберите категорию: ', reply_markup=categories)

@router.message(F.text == 'Статистика')
async def stats_handler(message: types.Message):
    stats = await get_my_stats(message.from_user.id)
    await message.answer(stats)