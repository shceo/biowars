# handlers/infect.py
"""Basic infection and vaccine purchase commands."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
import re

from aiogram import Router, types, F
from tortoise.exceptions import DoesNotExist

from services.lab_service import (
    get_player_cached,
    get_lab_cached,
    get_skill_cached,
    get_stats_cached,
    process_pathogens,
)
from models.player import Player
from utils.formatting import short_number

router = Router()

# ключ – (attacker_id, target_id), значение – время последнего заражения
_infection_cd: Dict[Tuple[int, int], datetime] = {}


@router.message(F.text.regexp(r'^заразить', flags=re.IGNORECASE))
async def infect_user(message: types.Message):
    """Infect another user consuming one pathogen."""
    attacker_id = message.from_user.id

    try:
        attacker_player = await get_player_cached(attacker_id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    attacker_lab = await get_lab_cached(attacker_player)
    attacker_stats = await get_stats_cached(attacker_lab)
    attacker_skills = await get_skill_cached(attacker_lab)
    await process_pathogens(attacker_lab, attacker_skills)

    now = datetime.now(timezone.utc)
    if attacker_lab.fever_until and attacker_lab.fever_until > now:
        return await message.answer(
            "Вы не можете заражать других, пока у вас горячка. Используйте !купить вакцину."
        )

    if attacker_lab.free_pathogens <= 0:
        return await message.answer("Нет свободных патогенов для заражения")

    # Determine target
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            return await message.answer("Укажите пользователя для заражения")
        ref = parts[1]
        if ref.startswith('@'):
            try:
                target_user = await message.bot.get_chat(ref)
            except Exception:
                return await message.answer("Не удалось найти пользователя")
        else:
            try:
                target_user = await message.bot.get_chat(int(ref))
            except Exception:
                return await message.answer("Не удалось найти пользователя")

    if target_user.id == attacker_id:
        return await message.answer("Нельзя заразить себя")

    cooldown_key = (attacker_id, target_user.id)
    last_attack = _infection_cd.get(cooldown_key)
    if last_attack and now - last_attack < timedelta(hours=3):
        remaining = timedelta(hours=3) - (now - last_attack)
        minutes_left = int(remaining.total_seconds() // 60)
        hours_left = minutes_left // 60
        minutes_left %= 60
        return await message.answer(
            "⏱️ Повторное заражение этого пользователя будет доступно через "
            f"<code>{hours_left} ч. {minutes_left} мин</code>.",
            parse_mode="HTML",
        )

    _infection_cd[cooldown_key] = now

    target_player, _ = await Player.get_or_create(
        telegram_id=target_user.id,
        defaults={"full_name": target_user.full_name},
    )
    target_lab = await get_lab_cached(target_player)
    target_stats = await get_stats_cached(target_lab)

    attacker_lab.free_pathogens -= 1
    await attacker_lab.save()

    fever_minutes = min(attacker_skills.lethality, 60)
    infection_days = attacker_skills.lethality
    target_lab.fever_until = now + timedelta(minutes=fever_minutes)
    target_lab.infection_until = now + timedelta(days=infection_days)
    await target_lab.save()

    attacker_stats.bio_experience += 1000
    await attacker_stats.save()
    target_stats.infected_count += 1
    await target_stats.save()

    attacker_link = f"<a href=\"tg://openmessage?user_id={attacker_id}\">{message.from_user.full_name}</a>"
    target_link = f"<a href=\"tg://openmessage?user_id={target_user.id}\">{target_user.full_name}</a>"

    pathogen_name = attacker_lab.pathogen_name
    if pathogen_name:
        pathogen_phrase = f"патогеном «{pathogen_name}»"
    else:
        pathogen_phrase = "неизвестным патогеном"

    text = (
        f"🦠 {attacker_link} подверг заражению {pathogen_phrase} {target_link}\n"
        f"<blockquote>☠️ Горячка на {fever_minutes} минут\n"
        f"🤒 Заражение на {infection_days} дней\n"
        f"☣️ +1k био-опыта</blockquote>"
    )
    await message.answer(text, parse_mode="HTML")

    try:
        await message.bot.send_message(
            target_user.id,
            (
                "🕵️‍♂️ Служба безопасности Вашей лаборатории докладывает:\n"
                "Была произведена как минимум 1 попытка Вашего заражения\n"
                f"Организатор заражения: {attacker_link}\n\n"
                f"<blockquote>🦠 {attacker_link} подверг заражению {pathogen_phrase} {target_link}⁬\n"
                f"☠️ Горячка на {fever_minutes} минут\n"
                f"🤒 Заражение на {infection_days} дней\n"
                f"☣️ +263 био-опыта</blockquote>"
            ),
            parse_mode="HTML",
        )
    except Exception:
        pass



@router.message(F.text.regexp(r'^!купить\s+вакцину$', flags=re.IGNORECASE))
async def buy_vaccine(message: types.Message):
    """Purchase a vaccine to cure fever."""
    user_id = message.from_user.id
    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    lab = await get_lab_cached(player)
    stats = await get_stats_cached(lab)

    now = datetime.now(timezone.utc)
    if not lab.fever_until or lab.fever_until <= now:
        return await message.answer("<b>📝 У вас нет горячки.</b>")

    seconds_left = int((lab.fever_until - now).total_seconds())
    price_per_second = 2000 / (60 * 60)
    cost = max(0, int(price_per_second * seconds_left))

    if cost > stats.bio_resource:
        return await message.answer("<b>❌ Не хватает био-ресурсов на вакцину.</b>")

    stats.bio_resource -= cost
    await stats.save()

    lab.fever_until = None
    await lab.save()

    await message.answer(
        f"💉 <b>Вы излечились от горячки.</b>\n"
        f"🧬 <b>Стоимость вакцины</b> : <code>{short_number(cost)}</code> био-ресурсов"
    )
