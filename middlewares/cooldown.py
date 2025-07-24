from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class CooldownMiddleware(BaseMiddleware):
    """Simple per-user cooldown for message processing."""

    def __init__(self, delay: float = 1.0) -> None:
        self.delay = delay
        self._last_call: Dict[int, datetime] = {}

    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        now = datetime.now(timezone.utc)
        last_time = self._last_call.get(user_id)
        if last_time and (now - last_time).total_seconds() < self.delay:
            return  # ignore message to prevent spam

        self._last_call[user_id] = now
        return await handler(event, data)
