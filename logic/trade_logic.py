import aiohttp
import asyncio
from database.engine import Session
from database.models import Products, Category
from sqlalchemy import select, distinct, text
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import smm_key

from sqlalchemy import select

async def add_products():
    async with aiohttp.ClientSession() as session:
        url = f'https://looksmm.ru/api/v2?action=services&key={smm_key}'
        async with session.get(url) as response:
            data_list = await response.json()
            
            with Session() as db_session:
                for data in data_list:
                    sid = int(data['service'])
                    cat_name = data['category'] # Имя категории из JSON

                    # --- ШАГ 1: Работаем с категорией ---
                    # Ищем категорию в нашей таблице Category по имени
                    category_obj = db_session.execute(
                        select(Category).where(Category.name == cat_name)
                    ).scalar_one_or_none()

                    if not category_obj:
                        # Если такой категории нет — создаем её!
                        category_obj = Category(name=cat_name)
                        db_session.add(category_obj)
                        db_session.flush() # flush() заставит БД выдать ID для новой категории прямо сейчас

                    # --- ШАГ 2: Работаем с продуктом ---
                    product = db_session.execute(
                        select(Products).where(Products.service_id == sid)
                    ).scalar_one_or_none()

                    if product:
                        # Обновляем существующий
                        product.name = data['name']
                        product.rate = data['rate']
                        product.category_id = category_obj.id # Привязываем актуальный ID
                    else:
                        # Создаем новый
                        new_product = Products(
                            service_id=sid,
                            name=data['name'],
                            category_id=category_obj.id,                         
                            network=data['network'],
                            type=data['type'],
                            rate=data['rate'],
                            min=data['min'],
                            max=data['max'],
                            description=data['description'],
                            refill=data['refill'],
                            canceling_is_available=data['canceling_is_available'],
                            cancel=data['cancel']
                        )
                        db_session.add(new_product)
                
                db_session.commit()

#asyncio.run(add_products())

def category_render(page: int = 0):
    builder = InlineKeyboardBuilder()
    limit = 10  # Сколько кнопок на странице
    offset = page * limit # Сколько пропустить

    with Session() as session:
        # 1. Считаем общее количество, чтобы знать, есть ли следующая страница
        total_count = session.query(Category).count()
        
        # 2. Берем только нужные 10 штук
        categories = session.execute(
            select(Category).offset(offset).limit(limit)
        ).scalars().all()

        # Добавляем основные кнопки категорий
        for cat in categories:
            builder.row(types.InlineKeyboardButton(
                text=cat.name, 
                callback_data=f"sel_cat_{cat.id}"
            ))

        # 3. Слой со стрелочками (навигация)
        nav_buttons = []
        
        # Если не первая страница — добавляем "Назад"
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"cat_page_{page - 1}"
            ))
        
        # Если есть еще данные дальше — добавляем "Вперед"
        if offset + limit < total_count:
            nav_buttons.append(types.InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"cat_page_{page + 1}"
            ))

        if nav_buttons:
            builder.row(*nav_buttons) # Распаковываем список кнопок в один ряд

        return builder.as_markup()
    
def products_render(category_id):
    builder = InlineKeyboardBuilder()
    with Session() as session:
        products = session.execute(select(Products).where(Products.category_id == category_id)).scalars().all()
        for p in products:
            builder.row(types.InlineKeyboardButton(text=f'{p.name}', callback_data=f'sel_product_{p.service_id}'))
        builder.row(types.InlineKeyboardButton(text='Назад', callback_data='back_to_category_sel'))
        return builder.as_markup()
    
def buy_product_render(service_id):
    builder = InlineKeyboardBuilder()
    with Session() as session:
        product = session.execute(select(Products).where(Products.service_id == service_id)).scalar_one_or_none()
        text = (
            f"📦 **{product.name}**\n\n"
            f"📝 Описание: {product.description or 'Нет описания'}\n"
            f"💰 Цена: {product.rate} руб. (за 1000 шт.)\n"
            f"📉 Мин. заказ: {product.min}\n"
            f"📈 Макс. заказ: {product.max}\n"
        )
        builder.row(types.InlineKeyboardButton(text='💳 Купить', callback_data='buy_{product.service.id}'))
        builder.row(types.InlineKeyboardButton(text='⬅️ Назад к категории', callback_data=f'sel_cat_{product.category_id}'))
        return(text, builder.as_markup())