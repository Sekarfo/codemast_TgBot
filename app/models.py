from datetime import datetime
from sqlalchemy import (Column,Integer,BigInteger,String,DateTime,Text,ForeignKey,)
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(Text, nullable=True)
    lang = Column(String(5), default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)


class UserState(Base):
    __tablename__ = "user_states"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    state = Column(String(50), nullable=False)          
    query_text = Column(Text, nullable=True)            
    page = Column(Integer, nullable=False, default=1)   
    updated_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    slug = Column(Text, unique=True, index=True, nullable=False)
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)         
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
