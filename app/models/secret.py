from backend.db import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import func




class Secret(Base):
    __tablename__ = 'secret'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    created_at = Column(DateTime, default=func.now())

