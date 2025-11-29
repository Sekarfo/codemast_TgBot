from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime,
    Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    lang = Column(String(5), default="ru")

    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

class UserState(Base):
    __tablename__ = "user_states"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    state = Column(String(50), nullable=False)   # 'MENU', 'WAIT_QUERY', 'SHOW_RESULTS'
    payload = Column(JSONB, nullable=True)       # {'query': '...', 'page': 1}
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String, nullable=True)     # "tag1,tag2,tag3"
    source_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
