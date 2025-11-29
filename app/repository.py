from datetime import datetime

from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User, UserState


def _get_session() -> Session:
    return SessionLocal()


def upsert_user_and_state_on_start(
    tg_id: int,
    username: str | None,
    lang_code: str | None,
) -> None:
    """
    Ensure there is a User and UserState for the given Telegram user.
    - If the user doesn't exist: create it.
    - If it exists: update username/lang and last_seen_at.
    - UserState is set to "MENU" on /start.
    """
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
            # Flush to get user.id for UserState FK
            session.flush()
        else:
            # Update existing user info
            if username:
                user.username = username
            if lang_code:
                user.lang = lang_code
            user.last_seen_at = now

        # Upsert state: PK of UserState is user_id
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


