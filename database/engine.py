from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import my_database

engine = create_engine(my_database)
Session = sessionmaker(bind=engine)