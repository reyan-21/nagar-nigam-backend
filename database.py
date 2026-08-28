from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Format: mysql+pymysql://username:password@localhost/database_name
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/nagar_nigam_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()