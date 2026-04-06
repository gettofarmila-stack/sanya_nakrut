from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import my_database, async_database

engine = create_engine(my_database)
Session = sessionmaker(bind=engine)

async_engine = create_async_engine(async_database)
AsyncSession = async_sessionmaker(bind=async_engine, expire_on_commit=False)