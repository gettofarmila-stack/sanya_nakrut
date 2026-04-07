
import asyncio
import random
from aiogram import types, F, Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from logic.topup_logic import select_payment_method_inline, get_now_price, create_payment, check_payment, adding_funds
from keyboards.topup_menus import confim_payment, update_payment
from database.models import Payment
from config import MY_ADDR

class TopUp(StatesGroup):
    waiting_for_amount = State()
    waiting_for_confirm = State()

router = Router()

@router.message(F.text == 'Пополнение')
async def topup_menu_handler(message: types.Message):
    await message.answer(f'Выбери способ пополнения:', reply_markup=select_payment_method_inline())

@router.callback_query(F.data == 'topup_usdtbnb')
async def topup_usdtbnb_first_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введи сумму пополнения в рублях:')
    await state.set_state(TopUp.waiting_for_amount)
    await callback.answer()

@router.message(TopUp.waiting_for_amount)
async def topup_usdtbnb_second_handler(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer('Нужно писать цифры! Попробуй ещё раз:')
    if int(message.text) < 100:
        return await message.answer('Минимальная сумма пополнения 100 рублей! Попробуй ещё раз:')
    amount = int(message.text)
    amount_usdt = await get_now_price(amount)
    amount_usdt = round(amount_usdt, 2)
    await state.update_data(user_amount=amount_usdt)
    await state.set_state(TopUp.waiting_for_confirm)
    await message.answer(f'Вы уверены что хотите пополнить баланс на {amount}р. через USDTBNB?', reply_markup=confim_payment())

@router.callback_query(TopUp.waiting_for_confirm, F.data == 'confirm_payment')
async def topup_usdtbnb_third_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data.get('user_amount')
    price += price * random.choice([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09])
    price = round(price, 2)
    payment_id = await create_payment(callback.from_user.id, price)
    await callback.message.edit_text(f'Оплачивай ровно {price}USDT по сети BNB на этот кошелёк\n{MY_ADDR}\nОплатил? Жми обновить', reply_markup=update_payment(payment_id))
    await state.clear()

@router.callback_query(F.data.startswith('check_'))
async def update_topup_handler(callback: types.CallbackQuery):
    payment_id = int(callback.data.split('_')[1])
    checked = await asyncio.to_thread(check_payment, payment_id)
    if checked:
        adding_funds(callback.from_user.id, payment_id)
        return await callback.answer('Успешно пополнен баланс!')
    else:
        return await callback.answer('Не получилось, повторите попытку...')
    
