import aiohttp
import asyncio
from aiogram import types
from database.engine import Session
from database.models import Products, Category, User
from sqlalchemy import select, distinct, text
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import smm_key
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select

async def add_products():
    async with aiohttp.ClientSession() as session:
        url = f'https://looksmm.ru/api/v2?action=services&key={smm_key}'
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Ошибка API: {response.status}")
                return
            
            data_list = await response.json()
            
            with Session() as db_session:
                for data in data_list:
                    sid = int(data['service'])
                    cat_name = data['category']

                    # --- ШАГ 1: Работаем с категорией ---
                    category_obj = db_session.execute(
                        select(Category).where(Category.name == cat_name)
                    ).scalar_one_or_none()

                    if not category_obj:
                        category_obj = Category(name=cat_name)
                        db_session.add(category_obj)
                        db_session.flush() # Получаем ID новой категории сразу

                    # --- ШАГ 2: Подготовка цены (наценка 10% через Decimal) ---
                    # Переводим в Decimal и умножаем на 1.1
                    raw_rate = Decimal(str(data['rate']))
                    markup = Decimal("1.1")
                    # Округляем до 4 знаков после запятой (Numeric(20, 4))
                    final_rate = (raw_rate * markup).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                    # --- ШАГ 3: Работаем с продуктом ---
                    product = db_session.execute(
                        select(Products).where(Products.service_id == sid)
                    ).scalar_one_or_none()

                    if product:
                        # Обновляем существующий товар
                        product.name = data['name']
                        product.rate = final_rate
                        product.category_id = category_obj.id
                        product.min = int(data['min'])
                        product.max = int(data['max'])
                        product.description = data.get('description', '')
                    else:
                        # Создаем новый товар
                        new_product = Products(
                            service_id=sid,
                            name=data['name'],
                            category_id=category_obj.id,                         
                            network=data.get('network', 'Unknown'),
                            type=data.get('type', 'Default'),
                            rate=final_rate,
                            min=int(data['min']),
                            max=int(data['max']),
                            description=data.get('description', ''),
                            refill=data.get('refill', False),
                            canceling_is_available=data.get('canceling_is_available', False),
                            cancel=data.get('cancel', False)
                        )
                        db_session.add(new_product)
                
                db_session.commit()
                print("✅ Все товары обновлены, наценка 10% применена!")

asyncio.run(add_products())

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
        builder.row(types.InlineKeyboardButton(text='💳 Купить', callback_data=f'buy_{product.service_id}'))
        builder.row(types.InlineKeyboardButton(text='⬅️ Назад к категории', callback_data=f'sel_cat_{product.category_id}'))
        return(text, builder.as_markup())
    
async def order_processing(uid, service_id, count_of_product, link, message: types.Message):
    with Session() as session:
        user = session.execute(select(User).where(User.user_id == uid)).scalar_one_or_none()
        product = session.execute(select(Products).where(Products.service_id == service_id)).scalar_one_or_none()
        if count_of_product < product.min:
            return(f'Слишком маленький заказ! Минимальный заказ у этого продукта {product.min}')
        order_sum = product.rate * count_of_product
        if user.stats.balance < order_sum:
            return(f'Недостаточно средств! Вам не хватает {order_sum - user.stats.balance}')
        user.stats.balance -= order_sum
        session.commit()
        async with aiohttp.ClientSession() as c_session:
            url = 'https://looksmm.ru/api/v2'
            params = {
                'key': smm_key,
                'action': 'add',
                'service': service_id,
                'link': link,
                'quantity': count_of_product
            }
            try:
                async with c_session.get(url, params=params) as response:
                    result = await response.json()
                    if "order" in result:
                        order_id = result["order"]
                        await message.answer(f"✅ Заказ создан! ID в системе: {order_id}")
                    else:
                        user.stats.balance += order_sum
                        session.commit()
                        await message.answer(f"❌ Ошибка сервиса: {result.get('error', 'Unknown')}. Деньги возвращены.")
                
            except Exception as e:
                user.stats.balance += order_sum
                session.commit()
                print(f"Ошибка: {e}")
                await message.answer("🛠 Техническая ошибка. Деньги возвращены на баланс.")

