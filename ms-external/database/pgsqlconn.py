from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv
from urllib.parse import quote 
import os
load_dotenv()
dbhost = os.getenv("DBHOST")
dbuser = os.getenv("DBUSERNAME")
dbpass = os.getenv("DBPASSWORD")
dbname = os.getenv("DBNAME")
dburl = f"postgresql+psycopg2://{dbuser}:{quote(dbpass)}@{dbhost}/{dbname}"
engine = create_engine(dburl, pool_pre_ping=True)


def db_session():
    dburl = f"postgresql+psycopg2://{dbuser}:{quote(dbpass)}@{dbhost}/{dbname}"
    engine = create_engine(dburl, pool_pre_ping=True)
    session  = Session(bind= engine)
    return session
    