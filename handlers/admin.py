# handlers/admin/boost.py
import re
from aiogram import Router, types, F
from tortoise.exceptions import DoesNotExist

from models.player import Player
from services.lab_service import get_lab_cached
from models.statistics import Statistics
from utils.formatting import short_number

ADMIN_IDS = {1806169479, 1194325722}
router = Router()

# Ловим команды вида ".буст <amount> <@username или ID>"
@router.message(F.text.regexp(r"^\.буст\s+\d+\s+\S+", flags=re.IGNORECASE))
async def cmd_boost(message: types.Message):
    # Разбираем аргументы
    match = re.match(r"^\.буст\s+(\d+)\s+(\S+)", message.text, flags=re.IGNORECASE)
    if not match:
        return  # невалидный формат

    if message.from_user.id not in ADMIN_IDS:
        return  # не админ — молчим

    amount   = int(match.group(1))
    user_ref = match.group(2).lstrip()  # либо "@username", либо "123456789"

    # Ищем игрока
    if user_ref.startswith("@"):
        username = user_ref[1:].lower()
        player = await Player.get_or_none(username=username)
        if not player:
            return await message.answer("Игрок с таким username не найден")
    else:
        try:
            tg_id = int(user_ref)
        except ValueError:
            return await message.answer("Укажите пользователя как @username или числовой ID")
        player = await Player.get_or_none(telegram_id=tg_id)
        if not player:
            return await message.answer("Игрок не найден")

    # Всё ок, выдаём ресурсы
    lab   = await get_lab_cached(player)
    stats = await Statistics.get(lab=lab)
    stats.bio_resource += amount
    await stats.save()

    await message.answer(
        f"✅ Админ выдал {short_number(amount)} био‑ресурсов игроку "
        f"<b>{player.username or player.telegram_id}</b>"
    )
