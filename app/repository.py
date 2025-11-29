from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Category, Item, User, UserState


def _get_session() -> Session:
    return SessionLocal()

def upsert_user_and_state_on_start(
    tg_id: int,
    username: str | None,
    lang_code: str | None,
) -> None:
    
    session = _get_session()
    now = datetime.utcnow()

    try:
        user = session.query(User).filter(User.tg_id == tg_id).one_or_none()
        if user is None:
            user = User(
                tg_id=tg_id,
                username=username,
                lang=lang_code or "ru",
                created_at=now,
                last_seen_at=now,
            )
            session.add(user)
            session.flush()
        else:
            if username:
                user.username = username
            if lang_code:
                user.lang = lang_code
            user.last_seen_at = now

        state = session.get(UserState, user.id)
        if state is None:
            state = UserState(
                user_id=user.id,
                state="MENU",
                query_text=None,
                page=1,
                updated_at=now,
            )
            session.add(state)
        else:
            state.state = "MENU"
            state.query_text = None
            state.page = 1
            state.updated_at = now

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def set_user_state(
    tg_id: int,
    new_state: str,
    query_text: str | None = None,
    page: int = 1,
) -> None:
    
    session = _get_session()
    now = datetime.utcnow()

    try:
        user = session.query(User).filter(User.tg_id == tg_id).one_or_none()
        if user is None:
            user = User(
                tg_id=tg_id,
                username=None,
                lang="ru",
                created_at=now,
                last_seen_at=now,
            )
            session.add(user)
            session.flush()
        else:
            user.last_seen_at = now

        state = session.get(UserState, user.id)
        if state is None:
            state = UserState(
                user_id=user.id,
                state=new_state,
                query_text=query_text,
                page=page,
                updated_at=now,
            )
            session.add(state)
        else:
            state.state = new_state
            state.query_text = query_text
            state.page = page
            state.updated_at = now

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_user_state(tg_id: int) -> Optional[UserState]:
    
    session = _get_session()
    try:
        user = session.query(User).filter(User.tg_id == tg_id).one_or_none()
        if user is None:
            return None
        state = session.get(UserState, user.id)
        if state is None:
            return None
        
        session.expunge(state)
        return state
    finally:
        session.close()


def list_categories() -> List[Category]:
    
    session = _get_session()
    try:
        cats = (
            session.query(Category)
            .order_by(Category.name.asc())
            .all()
        )
        return list(cats)
    finally:
        session.close()


def get_category(category_id: int) -> Optional[Category]:
    
    session = _get_session()
    try:
        category = session.get(Category, category_id)
        if category is not None:
            session.expunge(category)
        return category
    finally:
        session.close()


def get_category_items(
    category_id: int,
    page: int,
    page_size: int,
) -> Tuple[List[Item], bool]:
    
    session = _get_session()
    try:
        offset = max(page - 1, 0) * page_size
        query = (
            session.query(Item)
            .filter(Item.category_id == category_id)
            .order_by(Item.updated_at.desc())
            .offset(offset)
            .limit(page_size + 1)
        )
        items = list(query)
        has_next = len(items) > page_size
        return items[:page_size], has_next
    finally:
        session.close()


def get_latest_items(limit: int = 5) -> List[Item]:
   
    session = _get_session()
    try:
        items = (
            session.query(Item)
            .order_by(Item.updated_at.desc())
            .limit(limit)
            .all()
        )
        return list(items)
    finally:
        session.close()


def search_items(
    query: str,
    limit: int = 5,
) -> List[Item]:
    
    session = _get_session()

    try:
        q = (
            session.query(Item)
            .filter(
                or_(
                    Item.title.ilike(f"%{query}%"),
                    Item.content.ilike(f"%{query}%"),
                    Item.tags.ilike(f"%{query}%"),
                )
            )
            .order_by(Item.created_at.desc())
            .limit(limit)
        )
        items = list(q)
        return items
    finally:
        session.close()

