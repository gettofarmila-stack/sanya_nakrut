import asyncio
from aiogram import Router, F, types
from logic.trade_logic import category_render, products_render, buy_product_render, order_processing
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext



class OrderProcess(StatesGroup):
    waiting_for_link = State()     #  Ссылка
    waiting_for_count = State()    # Количество
router = Router()

@router.callback_query(F.data.startswith('back_to_category_sel'))
async def products_menu_open(callback: types.CallbackQuery):
    categories = await asyncio.to_thread(category_render, page=0)
    await callback.message.edit_reply_markup(reply_markup=categories)
    await callback.answer()

@router.callback_query(F.data.startswith("cat_page_"))
async def change_category_page(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
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
    await state.update_data(order_link=message.text)
    await state.set_state(OrderProcess.waiting_for_count)
    await message.answer("🔢 Теперь введите количество (только цифры):")

@router.message(OrderProcess.waiting_for_count)
async def get_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Нужно именно число! Попробуй еще раз:")
    count = int(message.text)
    data = await state.get_data()
    s_id = data['order_service_id']
    link = data['order_link']
    u_id = message.from_user.id
    result = await order_processing(int(u_id), int(s_id), int(count), link, message)
    if isinstance(result, str):
        await message.answer(result)
    await state.clear()