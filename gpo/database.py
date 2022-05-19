"""
Db Connection for GPO
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from gpo import settings

# Sqlalchemy requires 'postgresql' as the protocol
uri = settings.DB_URI.replace("postgres://", "postgresql://", 1)

schema_name = "gpo"

engine = create_engine(uri, connect_args={"options": f"-csearch_path={schema_name}"})

if not engine.dialect.has_schema(engine, schema_name):
    engine.execute(CreateSchema(schema_name))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()
