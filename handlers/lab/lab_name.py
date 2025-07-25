from aiogram import Router, types, F
import re

from utils.validation import contains_link_or_mention
from tortoise.exceptions import DoesNotExist

from services.lab_service import get_player_cached, get_lab_cached
from models.laboratory import Laboratory

router = Router()

@router.message(F.text.regexp(r'^-лаб$', flags=re.IGNORECASE))
async def clear_lab_name(message: types.Message):
    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    lab = await get_lab_cached(player)
    lab.lab_name = None
    await lab.save()

    await message.answer("❎ Название лаборатории удалено")


@router.message(F.text.regexp(r'^\.имя\s+лабы\s+.+', flags=re.IGNORECASE))
async def set_lab_name(message: types.Message):
    match = re.match(r'^\.имя\s+лабы\s+(.+)$', message.text, flags=re.IGNORECASE)
    if not match:
        return

    name = match.group(1).strip()
    if len(name) > 30:
        return await message.answer("❌ Имя лаборатории должно быть не длиннее 30 символов.")

    if contains_link_or_mention(name):
        return await message.answer("📋 Ссылки в имени лаборатории запрещены.")

    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    exists = await Laboratory.filter(lab_name__iexact=name).exists()
    if exists:
        return await message.answer("🗓 Такое имя лаборатории уже существует!")

    lab = await get_lab_cached(player)
    lab.lab_name = name
    await lab.save()

    await message.answer("<b>✅ Имя лаборатории обновлено.</b>")
