import asyncio
import logging
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram import Router, F, types
from logic.user_logic import registration, is_user
from keyboards.main_menu import main_menu_kb, profile_kb, orders_kb
from logic.trade_logic import category_render, products_render, buy_product_render, order_processing
from logic.order_logic import get_my_orders, get_my_order, inline_keyboards_order, update_order, refill_order, get_my_old_orders, inline_keyboards_old_order
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

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
    await message.answer(f'Ваши заказы: ', reply_markup=orders)

@router.message(F.text == 'История заказов')
async def old_orders_hand(message: types.Message):
    orders = await asyncio.to_thread(get_my_old_orders, message.from_user.id)
    await message.answer(f'Ваши заказы: ', reply_markup=orders)

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

@router.message(F.text == 'Реферальная система')
async def ref_system_handler(message: types.Message):
    bot_info = await message.bot.get_me()
    await message.answer(f'Приглашая друга, вы получаете 1% с каждого его пополнения!\nВаша реферальная ссылка:\nhttps://t.me/{bot_info.username}?start={message.from_user.id}')

@router.message(F.text == 'Товары')
async def products_one_menu_open(message: types.Message):
    categories = await asyncio.to_thread(category_render, page=0)
    await message.answer('Выберите категорию: ', reply_markup=categories)

@router.callback_query(F.data.startswith('back_to_category_sel'))
async def products_menu_open(callback: types.CallbackQuery):
    categories = await asyncio.to_thread(category_render, page=0)
    await callback.message.edit_reply_markup(reply_markup=categories)
    await callback.answer()

@router.callback_query(F.data.startswith("cat_page_"))
async def change_category_page(callback: types.CallbackQuery):
    # Достаем номер страницы из колбэка
    page = int(callback.data.split("_")[-1])
    
    # Генерируем новую клавиатуру для этой страницы
    markup = await asyncio.to_thread(category_render, page=page)
    
    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith('sel_cat_'))
async def select_category_inline(callback: types.CallbackQuery):
    id = int(callback.data.split('_')[-1])
    markup = await asyncio.to_thread(products_render, category_id=id)
    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith('sel_product_'))
async def select_product_inline(callback: types.CallbackQuery):
    product_id = int(callback.data.split('_')[-1])
    info_text, keyboard = await asyncio.to_thread(buy_product_render, product_id)
    await callback.message.edit_text(text=info_text, reply_markup=keyboard, parse_mode="HTML") 
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def start_buy(callback: types.CallbackQuery, state: FSMContext):
    service_id = callback.data.split("_")[1]
    await state.update_data(order_service_id=service_id)
    await state.set_state(OrderProcess.waiting_for_link)   
    await callback.message.answer("🔗 Пришлите ссылку на объект накрутки (профиль/пост):")
    await callback.answer()

@router.message(OrderProcess.waiting_for_link)
async def get_link(message: types.Message, state: FSMContext):
    # Сохраняем ссылку в черновик
    await state.update_data(order_link=message.text)
    
    # Переключаем на ожидание количества
    await state.set_state(OrderProcess.waiting_for_count)
    
    await message.answer("🔢 Теперь введите количество (только цифры):")

@router.message(OrderProcess.waiting_for_count)
async def get_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Нужно именно число! Попробуй еще раз:")

    count = int(message.text)
    
    # Вытаскиваем всё, что накопили в черновике
    data = await state.get_data()
    s_id = data['order_service_id']
    link = data['order_link']
    u_id = message.from_user.id

    # ВЫЗЫВАЕМ ТВОЮ ФУНКЦИЮ (про которую мы говорили выше)
    # Важно: вызываем через await, так как она асинхронная!
    result = await order_processing(int(u_id), int(s_id), int(count), link, message)
    
    # Если функция вернула строку (ошибку) — выводим её
    if isinstance(result, str):
        await message.answer(result)
    
    # Очищаем состояние, чтобы юзер мог снова пользоваться ботом
    await state.clear()