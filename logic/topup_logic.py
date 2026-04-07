
import aiohttp
import asyncio
import logging
from web3 import Web3
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.engine import AsyncSession, Session
from database.models import User, Payment
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config import MY_ADDR


RPC_URL = "https://bsc-mainnet.nodereal.io/v1/6a73e9175e6745dea810cb0af3575810"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
USDT_CONTRACT = w3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")
TRANSFER_EVENT_HASH = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def get_incoming_usdt(depth=5000):
    my_address = MY_ADDR
    my_addr_padded = "0x" + my_address.lower()[2:].zfill(64)
    latest_block = w3.eth.block_number
    logs = w3.eth.get_logs({
        "fromBlock": latest_block - depth,
        "toBlock": "latest",
        "address": USDT_CONTRACT,
        "topics": [TRANSFER_EVENT_HASH, None, my_addr_padded]
    })
    logging.info(f"Проверено {depth} блоков. Найдено транзакций: {len(logs)}")
    values = []
    for log in logs:
        value = int(log['data'].hex(), 16) / 10**18
        sender = "0x" + log['topics'][1].hex()[-40:]
        tx_hash = log['transactionHash'].hex()
        
        logging.info(f"💰 Входящий: {value} USDT")
        logging.info(f"   От: {sender}")
        logging.info(f"   Хэш: {tx_hash}")
        logging.info("-" * 30)
        values.append(value)
    if values:
        return(values)
    else:
        return None
def select_payment_method_inline():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='USDT BNB', callback_data='topup_usdtbnb'))
    return builder.as_markup()

async def get_now_price(sum):
    async with aiohttp.ClientSession() as session:
        url = 'https://api.binance.com/api/v3/ticker/price'
        async with session.get(url, params={'symbol': 'USDTRUB'}) as response:
            data = await response.json()
            price = float(data['price'])
            return(price / sum)

async def create_payment(uid, sum):
    async with AsyncSession() as session:
        res_user = await session.execute(select(User).where(User.user_id == uid))
        user = res_user.scalar_one_or_none()
        await get_now_price(sum)

def check_payment(payment_id):
    with Session() as session:
        payment_res = session.execute(select(Payment).where(Payment.id == payment_id))
        payment = payment_res.scalar_one_or_none()
        payment_sum = payment.topup_sum
        incomming_payments = get_incoming_usdt(5000)
        if incomming_payments is None:
            return False
        if payment_sum in incomming_payments:
            return True
        else: 
            return False

async def create_payment(uid, payment_total):
    async with AsyncSession() as session:
        new_payment = Payment(owner_id=uid, topup_sum=payment_total)
        session.add(new_payment)
        await session.commit()
        await session.refresh(new_payment)
        return new_payment.id
    
async def adding_funds(uid, payment_id):
    async with AsyncSession() as session:
        user_res = await session.execute(select(User).options(selectinload(User.stats)).where(User.user_id == uid))
        user = user_res.scalar_one_or_none()
        payment_res = await session.execute(select(Payment).where(Payment.owner_id == uid, Payment.id == int(payment_id)))
        payment = payment_res.scalar_one_or_none()
        user.stats.balance += payment.topup_sum
        payment.is_completed = True
        ref = user.referrer_id
        if ref:
            refer = await session.execute(select(User).options(selectinload(User.stats)).where(User.user_id == int(ref)))
            referrer = refer.scalar_one_or_none()
            referrer.stats.balance += (payment.topup_sum * 0.01)
        await session.commit()