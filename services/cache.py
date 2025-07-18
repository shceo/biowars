from typing import Dict, Any, Tuple
import asyncio
import time
from tortoise.exceptions import DoesNotExist

from models.player import Player
from models.laboratory import Laboratory
from models.skill import Skill
from models.statistics import Statistics
from models.pathogen import Pathogen

class LabCache:
    """Simple async cache for laboratory data."""
    def __init__(self) -> None:
        self._cache: Dict[int, Tuple[float, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self.ttl = 60  # seconds

    async def get_lab_data(self, user_id: int) -> Dict[str, Any]:
        async with self._lock:
            cached = self._cache.get(user_id)
            if cached and time.time() - cached[0] < self.ttl:
                return cached[1]

        player = await Player.get(telegram_id=user_id)
        lab = await Laboratory.get(player=player).prefetch_related("stats", "corporation")
        stats = await lab.stats
        skills = await Skill.get(lab=lab)
        pathogen = await Pathogen.filter(lab=lab).order_by("-created_at").first()
        data = {
            "player": player,
            "lab": lab,
            "stats": stats,
            "skills": skills,
            "pathogen": pathogen,
        }
        async with self._lock:
            self._cache[user_id] = (time.time(), data)
        return data

    async def invalidate(self, user_id: int) -> None:
        async with self._lock:
            self._cache.pop(user_id, None)

lab_cache = LabCache()
