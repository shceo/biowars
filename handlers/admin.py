from aiogram import Router, types, F
import re

from models.player import Player
from services.lab_service import get_lab_cached
from models.statistics import Statistics

ADMIN_IDS = {1806169479, 1194325722}

router = Router()

@router.message(F.text.regexp(r"^\.буст\s+\d+\s+\S+", flags=re.IGNORECASE))
async def cmd_boost(message: types.Message):
    # внутри разбираем
    match = re.match(r"^\.буст\s+(\d+)\s+(\S+)", message.text, flags=re.IGNORECASE)
    if not match:
        return

    if message.from_user.id not in ADMIN_IDS:
        return

    amount = int(match.group(1))
    user_ref = match.group(2)
    if not user_ref:
        return await message.answer("Укажите пользователя в формате @username или ID")

    target_id = None
    if user_ref.startswith("@"):
        try:
            chat = await message.bot.get_chat(user_ref)
            target_id = chat.id
        except Exception:
            return await message.answer("Не удалось определить пользователя")
    else:
        try:
            target_id = int(user_ref)
        except ValueError:
            return await message.answer("Неверный формат пользователя")

    player = await Player.get_or_none(telegram_id=target_id)
    if not player:
        return await message.answer("Игрок не найден")

    lab = await get_lab_cached(player)
    stats = await Statistics.get(lab=lab)
    stats.bio_resource += amount
    await stats.save()

    await message.answer(f"Выдано {amount} био-ресурсов пользователю {user_ref}")
