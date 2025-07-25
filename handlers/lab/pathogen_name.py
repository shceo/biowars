from aiogram import Router, types, F
import re

from utils.validation import contains_link_or_mention
from tortoise.exceptions import DoesNotExist
from services.lab_service import get_player_cached, get_lab_cached
from models.laboratory import Laboratory

router = Router()

# Команда для скрытия имени патогена
@router.message(F.text.regexp(r'^-имя\s+патогена$', flags=re.IGNORECASE))
async def clear_pathogen_name(message: types.Message):
    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    lab = await get_lab_cached(player)
    lab.pathogen_name = None
    await lab.save()

    await message.answer("❎ Название патогена засекречено")

# Команда для установки нового имени патогена
@router.message(F.text.regexp(r'^\.имя\s+патогена\s+.+', flags=re.IGNORECASE))
async def set_pathogen_name(message: types.Message):
    match = re.match(r'^\.имя\s+патогена\s+(.+)$', message.text, flags=re.IGNORECASE)
    if not match:
        return

    name = match.group(1).strip()

    # Проверка длины
    if len(name) > 20:
        return await message.answer("❌ Имя патогена должно быть не длиннее 20 символов.")

    # Запрещаем ссылки и упоминания
    if contains_link_or_mention(name):
        return await message.answer("📋 Ссылки в имени патогена запрещены.")

    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    # Проверка дубликата в базе
    exists = await Laboratory.filter(pathogen_name__iexact=name).exists()
    if exists:
        return await message.answer(
            "📝 Такое название патогена уже существует\n\n"
            "💬 Но Вы сможете получить это название, если Ваша лаборатория будет иметь больше био-опыта в десятки раз."
        )

    lab = await get_lab_cached(player)
    lab.pathogen_name = name
    await lab.save()

    await message.answer(
        f"✅ Название патогена изменено на «{name}»",
        parse_mode="HTML"
    )
