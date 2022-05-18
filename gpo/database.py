"""
Db Connection for GPO
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from gpo import settings

#Sqlalchemy the 'postgresql' as the protocol
uri = settings.DB_URI.replace("postgres://", "postgresql://", 1)

engine = create_engine(uri, connect_args={"options": "-csearch_path=gpo"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()
