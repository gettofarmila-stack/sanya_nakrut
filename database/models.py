from sqlalchemy import Integer, String, ForeignKey, Column, BigInteger, Boolean, Numeric, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from database.engine import engine
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)
    user_id = Column(BigInteger, nullable=False, unique=True)
    referrer_id = Column(BigInteger)

    stats = relationship('Stats', back_populates='user', uselist=False)
    orders = relationship('Order', back_populates='user')

class Stats(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), unique=True)
    balance = Column(Numeric(10, 2), default=0.00)
    total_spend = Column(BigInteger, default=0, nullable=False)

    user = relationship('User', back_populates='stats')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    # Связь: говорим Алхимии, что у категории есть список товаров
    products = relationship('Products', back_populates='category_rel')

class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, nullable=False)
    name = Column(String)
    type = Column(String)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category_rel = relationship('Category', back_populates='products')
    network = Column(String)
    description = Column(String)
    rate = Column(Numeric(precision=20, scale=4))
    min = Column(Integer)
    max = Column(Integer)
    refill = Column(Boolean)
    canceling_is_available = Column(Boolean)
    cancel = Column(Boolean)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_id = Column(BigInteger)
    owner_id = Column(BigInteger, ForeignKey('users.user_id'))
    order_sum = Column(Numeric(10, 2), nullable=False)
    service_id = Column(Integer)
    started_at = Column(DateTime, default=datetime.now)
    status = Column(String)
    remains = Column(Integer)
    update_cooldown = Column(DateTime)

    user = relationship('User', back_populates='orders')

Base.metadata.create_all(engine)