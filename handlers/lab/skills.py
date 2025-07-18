from aiogram import Router, types, F
from tortoise.exceptions import DoesNotExist

from services.lab_service import (
    get_player_cached,
    get_lab_cached,
    get_skill_cached,
    get_stats_cached,
)
from keyboards.lab_kb import confirm_keyboard, hide_keyboard


UPGRADE_PARAMS = {
    "infectivity": {
        "emoji": "🦠",
        "name": "заразности патогена",
        "base_cost": 5,
        "growth": 2.5,
        "command": "++зз",
    },
    "immunity": {
        "emoji": "🛡",
        "name": "иммунитета",
        "base_cost": 5,
        "growth": 2.6,
        "command": "++иммунитет",
    },
    "lethality": {
        "emoji": "☠️",
        "name": "летальности",
        "base_cost": 3,
        "growth": 1.95,
        "command": "++летальность",
    },
    "safety": {
        "emoji": "🕵️‍♂️",
        "name": "безопасности",
        "base_cost": 4,
        "growth": 2.09,
        "command": "++безопасность",
    },
    "qualification": {
        "emoji": "👨‍🔬",
        "name": "квалификации",
        "base_cost": 6,
        "growth": 2.4,
        "command": "++квалификация",
    },
    "pathogen": {
        "emoji": "🧪",
        "name": "патогена",
        "base_cost": 4,
        "growth": 2.0,
        "command": "++патоген",
    },
}


def calc_cost(field: str, level: int) -> int:
    """Return price for upgrading `field` from `level` to `level + 1`."""
    params = UPGRADE_PARAMS[field]
    base = params["base_cost"]
    growth = params["growth"] / 100
    price = base * ((1 + growth) ** (level - 1))
    return int(round(price))

router = Router()

@router.callback_query(F.data.startswith("upgrade:"))
async def upgrade_skill(callback: types.CallbackQuery):
    """Show confirmation dialog for skill upgrade."""
    user_id = callback.from_user.id

    try:
        _, field, owner_str = callback.data.split(":", 2)
    except ValueError:
        return await callback.answer("Неизвестный параметр", show_alert=True)

    if int(owner_str) != user_id:
        return await callback.answer("не шали, шалунишка", show_alert=True)

    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await callback.answer("Сначала отправьте /start", show_alert=True)

    lab = await get_lab_cached(player)
    skills = await get_skill_cached(lab)

    params = UPGRADE_PARAMS.get(field)
    if not params:
        return await callback.answer("Неизвестный параметр", show_alert=True)

    current = getattr(skills, field, 0) if field != "pathogen" else lab.max_pathogens
    cost = calc_cost(field, current)
    text = (
        f"<b>{params['emoji']} Прокачка {params['name']} на 1 ур (до {current + 1})\n"
        f"🧬 Цена: {cost} био-ресурсов</b>\n\n"
        f"<b><i>Команда: \"</i></b><code>{params['command']} {current + 1}</code><b><i>\"</i></b>"
    )

    await callback.message.answer(text, reply_markup=confirm_keyboard(field, user_id))
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:"))
async def confirm_upgrade(callback: types.CallbackQuery):
    """Apply upgrade after confirmation."""
    user_id = callback.from_user.id

    try:
        _, field, owner_str = callback.data.split(":", 2)
    except ValueError:
        return await callback.answer("Неизвестный параметр", show_alert=True)

    if int(owner_str) != user_id:
        return await callback.answer("не шали, шалунишка", show_alert=True)

    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await callback.answer("Сначала отправьте /start", show_alert=True)

    lab = await get_lab_cached(player)
    skills = await get_skill_cached(lab)
    stats = await get_stats_cached(lab)

    params = UPGRADE_PARAMS.get(field)
    if not params:
        return await callback.answer("Неизвестный параметр", show_alert=True)

    current = getattr(skills, field, 0) if field != "pathogen" else lab.max_pathogens
    cost = calc_cost(field, current)

    if stats.bio_resource < cost:
        return await callback.answer("Недостаточно био-ресурсов", show_alert=True)

    stats.bio_resource -= cost
    await stats.save()

    if field == "pathogen":
        old_value = lab.max_pathogens
        lab.max_pathogens += 1
        lab.free_pathogens += 1
        await lab.save()
    else:
        old_value = getattr(skills, field, 0)
        setattr(skills, field, old_value + 1)
        await skills.save()

    text = (
        f"{params['emoji']} Усиление {params['name']} на {old_value} ур (до {old_value + 1}) выполнено \n"
        f"🎉 Потрачено: 🧬 {cost} био-ресурсов"
    )

    await callback.message.edit_text(text, reply_markup=hide_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hide")
async def hide_message(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()
