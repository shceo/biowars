from aiogram import Router, types, F
import re
from tortoise.exceptions import DoesNotExist
from services.lab_service import get_player_cached, get_lab_cached

router = Router()

@router.message(F.text.regexp(r'^\.имя\s+патогена\s+.+', flags=re.IGNORECASE))
async def set_pathogen_name(message: types.Message):
    match = re.match(r'^\.имя\s+патогена\s+(.+)', message.text, flags=re.IGNORECASE)
    if not match:
        return

    name = match.group(1).strip()
    # Ограничение длины — не более 20 символов
    if len(name) > 20:
        return await message.answer(
            "❌ Имя патогена должно быть не длиннее 20 символов."
        )

    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer(
            "Сначала отправьте /start, чтобы зарегистрироваться."
        )

    lab = await get_lab_cached(player)
    lab.pathogen_name = name
    await lab.save()

    await message.answer(
        f"✅ Имя патогена установлено на <code>{name}</code>",
        parse_mode="HTML"
    )
