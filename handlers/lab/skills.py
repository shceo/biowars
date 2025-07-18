from aiogram import Router, types, F
from tortoise.exceptions import DoesNotExist

from services.lab_service import (
    get_player_cached,
    get_lab_cached,
    get_skill_cached,
)

router = Router()

@router.callback_query(F.data.startswith("upgrade:"))
async def upgrade_skill(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await callback.answer("Сначала отправьте /start", show_alert=True)

    lab = await get_lab_cached(player)
    skills = await get_skill_cached(lab)

    _, field = callback.data.split(":", 1)

    if field == "pathogen":
        lab.max_pathogens += 1
        lab.free_pathogens += 1
        await lab.save()
    else:
        value = getattr(skills, field, None)
        if value is None:
            return await callback.answer("Неизвестный параметр", show_alert=True)
        setattr(skills, field, value + 1)
        await skills.save()

    await callback.answer("Улучшено")
