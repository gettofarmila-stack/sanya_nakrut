import logging
from database.engine import Session, AsyncSession
from database.models import User, Stats
from sqlalchemy import select
from sqlalchemy.orm import selectinload

def registration(name, username, uid, referrer_id=None):
    with Session() as session:
        user = session.execute(select(User).where(User.user_id == uid)).scalar_one_or_none()
        if user:
            logging.warning(f'Юзер {uid} уже есть в базе')
            return False
        else:    
            new_user = User(name=name, username=username, user_id = uid, referrer_id=referrer_id)
            new_stats = Stats(balance=0, total_spend=0)
            new_user.stats = new_stats
            session.add(new_user)
            session.commit()
            logging.info(f'Юзер под айди {uid} зарегестрирован!')
            return True
        
def is_user(uid):
    with Session() as session:
        user = session.execute(select(User).where(User.user_id == uid)).scalar_one_or_none()
        return user
    
async def get_my_stats(uid):
    async with AsyncSession() as session:
        result = await session.execute(select(User).options(selectinload(User.stats)).where(User.user_id == uid))
        user = result.scalar_one_or_none()
        if user.referrer_id:
            info = f'Вас пригласил {user.referrer_id}id'
        else:
            info = f'Вас никто не приглашал, вы нашли нас сами'
        return f'''
        СТАТИСТИКА:
Ваш баланс: {user.stats.balance}
Всего потрачено: {user.stats.total_spend}
{info}
'''