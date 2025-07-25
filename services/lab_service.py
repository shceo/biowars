from typing import Dict, Tuple
import time

from tortoise.exceptions import DoesNotExist

from models.player import Player
from models.laboratory import Laboratory
from models.skill import Skill
from models.statistics import Statistics
from models.infection import Infection

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

from datetime import datetime, timedelta, timezone


def pathogen_interval(qualification: int) -> int:
    """Return minutes required to create a pathogen for given qualification level."""
    return max(1, 60 - (qualification - 1))


async def process_pathogens(lab: Laboratory, skills: Skill) -> None:
    """Update lab.free_pathogens based on timers and skills."""
    now = datetime.now(timezone.utc)
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


async def register_player_if_needed(tg_id: int, full_name: str) -> Player:
    """Return Player object creating initial lab if needed."""
    player, created = await Player.get_or_create(
        telegram_id=tg_id,
        defaults={"full_name": full_name},
    )

    if created:
        now = datetime.now(timezone.utc)
        default_name = f"им. {full_name}"[:30]
        lab = await Laboratory.create(
            player=player,
            free_pathogens=10,
            max_pathogens=10,
            next_pathogen_at=now + timedelta(minutes=60),
            lab_name=default_name,
        )
        await Skill.create(
            lab=lab,
            infectivity=1,
            immunity=1,
            lethality=1,
            safety=1,
            qualification=1,
        )
        await Statistics.create(lab=lab)
        # prime caches with newly created objects
        expires = time.time() + _CACHE_TTL
        _player_cache[tg_id] = (player, expires)
        _lab_cache[player.id] = (lab, expires)

    return player


async def cleanup_expired_infections(lab: Laboratory) -> None:
    """Remove expired infections related to this lab and update stats."""
    now = datetime.now(timezone.utc)
    expired_attacks = await Infection.filter(attacker_lab=lab, expires_at__lte=now).prefetch_related("target_lab")
    for inf in expired_attacks:
        stats = await get_stats_cached(lab)
        target_stats = await get_stats_cached(inf.target_lab)
        stats.infected_count = max(0, stats.infected_count - 1)
        target_stats.own_diseases = max(0, target_stats.own_diseases - 1)
        await stats.save()
        await target_stats.save()
        await inf.delete()
        active_other = await Infection.filter(target_lab=inf.target_lab, expires_at__gt=now).exists()
        if not active_other:
            inf.target_lab.infection_until = None
            await inf.target_lab.save()

    expired_defenses = await Infection.filter(target_lab=lab, expires_at__lte=now).prefetch_related("attacker_lab")
    for inf in expired_defenses:
        stats = await get_stats_cached(lab)
        attacker_stats = await get_stats_cached(inf.attacker_lab)
        attacker_stats.infected_count = max(0, attacker_stats.infected_count - 1)
        stats.own_diseases = max(0, stats.own_diseases - 1)
        await attacker_stats.save()
        await stats.save()
        await inf.delete()

    active = await Infection.filter(target_lab=lab, expires_at__gt=now).exists()
    if not active and lab.infection_until and lab.infection_until <= now:
        lab.infection_until = None
        await lab.save()


async def register_infection(attacker_lab: Laboratory, target_lab: Laboratory, duration_days: int) -> None:
    """Register a new infection ensuring unique counts and handling replacements."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=duration_days)

    existing = await Infection.filter(attacker_lab=attacker_lab, target_lab=target_lab, expires_at__gt=now).first()
    if existing:
        existing.expires_at = expires_at
        await existing.save()
        return

    other = await Infection.filter(target_lab=target_lab, expires_at__gt=now).first()
    if other:
        old_attacker_stats = await get_stats_cached(other.attacker_lab)
        target_stats = await get_stats_cached(target_lab)
        old_attacker_stats.infected_count = max(0, old_attacker_stats.infected_count - 1)
        target_stats.own_diseases = max(0, target_stats.own_diseases - 1)
        await old_attacker_stats.save()
        await target_stats.save()
        await other.delete()

    await Infection.create(attacker_lab=attacker_lab, target_lab=target_lab, expires_at=expires_at)
    target_lab.infection_until = expires_at
    await target_lab.save()
    attacker_stats = await get_stats_cached(attacker_lab)
    target_stats = await get_stats_cached(target_lab)
    attacker_stats.infected_count += 1
    target_stats.own_diseases += 1
    await attacker_stats.save()
    await target_stats.save()
