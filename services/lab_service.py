from typing import Dict, Tuple
import time

from tortoise.exceptions import DoesNotExist

from models.player import Player
from models.laboratory import Laboratory
from models.skill import Skill
from models.statistics import Statistics

# Простое кеширование в памяти, чтобы не обращаться к БД каждый раз
_CACHE_TTL = 60  # секунды
_player_cache: Dict[int, Tuple[Player, float]] = {}
_lab_cache: Dict[int, Tuple[Laboratory, float]] = {}
_skill_cache: Dict[int, Tuple[Skill, float]] = {}
_stats_cache: Dict[int, Tuple[Statistics, float]] = {}


async def get_player_cached(tg_id: int) -> Player:
    """Возвращает объект Player с кешированием."""
    now = time.time()
    cached = _player_cache.get(tg_id)
    if cached and cached[1] > now:
        return cached[0]
    player = await Player.get(telegram_id=tg_id)
    _player_cache[tg_id] = (player, now + _CACHE_TTL)
    return player


async def get_lab_cached(player: Player) -> Laboratory:
    """Возвращает лабораторию игрока с кешированием."""
    now = time.time()
    cached = _lab_cache.get(player.id)
    if cached and cached[1] > now:
        return cached[0]
    lab = await Laboratory.get(player=player).prefetch_related("corporation", "stats")
    _lab_cache[player.id] = (lab, now + _CACHE_TTL)
    return lab


async def get_skill_cached(lab: Laboratory) -> Skill:
    """Возвращает навыки лаборатории с кешированием."""
    now = time.time()
    cached = _skill_cache.get(lab.id)
    if cached and cached[1] > now:
        return cached[0]
    skill = await Skill.get(lab=lab)
    _skill_cache[lab.id] = (skill, now + _CACHE_TTL)
    return skill


async def get_stats_cached(lab: Laboratory) -> Statistics:
    """Возвращает статистику лаборатории с кешированием."""
    now = time.time()
    cached = _stats_cache.get(lab.id)
    if cached and cached[1] > now:
        return cached[0]
    stats = await lab.stats
    _stats_cache[lab.id] = (stats, now + _CACHE_TTL)
    return stats

from datetime import datetime, timedelta


def pathogen_interval(qualification: int) -> int:
    """Return minutes required to create a pathogen for given qualification level."""
    return max(1, 60 - (qualification - 1))


async def process_pathogens(lab: Laboratory, skills: Skill) -> None:
    """Update lab.free_pathogens based on timers and skills."""
    now = datetime.utcnow()
    interval = pathogen_interval(skills.qualification)

    if lab.free_pathogens >= lab.max_pathogens:
        lab.next_pathogen_at = None
        await lab.save()
        return

    if lab.next_pathogen_at is None:
        lab.next_pathogen_at = now + timedelta(minutes=interval)

    while lab.next_pathogen_at and lab.next_pathogen_at <= now and lab.free_pathogens < lab.max_pathogens:
        lab.free_pathogens += 1
        lab.next_pathogen_at += timedelta(minutes=interval)

    if lab.free_pathogens >= lab.max_pathogens:
        lab.next_pathogen_at = None

    await lab.save()
