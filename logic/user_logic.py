import logging
from database.engine import Session
from database.models import User, Stats
from sqlalchemy import select

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