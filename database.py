import os
import ssl
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/nagarnigam")

# Aiven Cloud ke SSL Certificate Error ko bypass karne ka logic
custom_args = {}
if "aivencloud" in SQLALCHEMY_DATABASE_URL:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    custom_args = {"ssl": ctx}

# engine mein custom_args pass kar diye
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=custom_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()