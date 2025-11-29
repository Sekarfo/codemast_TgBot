import os
from typing import Optional
from openai import OpenAI


SYSTEM_PROMPT = (
    "Ты — виртуальный помощник, который отвечает исключительно на русском языке "
    "и только на вопросы об экосистеме ,экосистемных сервисах, продуктах, "
    "обучении и связанных инициативах. Если запрос не относится к этой теме ТОГДА ОТВЕЧАЙ СТРОГО ВОТ ТАК: *я могу ответить только на вопросы об экосистеме, экосистемных сервисах, продуктах, обучении и связанных инициативах.* "
)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _client = OpenAI(api_key=api_key)
    return _client


def ask_ecosystem_bot(question: str) -> str:
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        temperature=0.32,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )

    return response.choices[0].message.content.strip()

