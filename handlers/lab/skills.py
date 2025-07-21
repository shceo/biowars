from aiogram import Router, types, F
import re
from tortoise.exceptions import DoesNotExist

from services.lab_service import (
    get_player_cached,
    get_lab_cached,
    get_skill_cached,
    get_stats_cached,
    process_pathogens,
)
from utils.formatting import short_number
from keyboards.lab_kb import confirm_keyboard, hide_keyboard

UPGRADE_PARAMS = {
    "infectivity": {
        "emoji": "🦠",
        "name": "заразности патогена",
        "growth": 2.5,
        "command": "++зз",
    },
    "immunity": {
        "emoji": "🛡",
        "name": "иммунитета",
        "growth": 2.6,
        "command": "++иммунитет",
    },
    "lethality": {
        "emoji": "☠️",
        "name": "летальности",
        "growth": 1.95,
        "command": "++летальность",
    },
    "safety": {
        "emoji": "🕵️‍♂️",
        "name": "безопасности",
        "growth": 2.09,
        "command": "++безопасность",
    },
    "qualification": {
        "emoji": "👨‍🔬",
        "name": "квалификации",
        "growth": 2.4,
        "command": "++квалификация",
    },
    "pathogen": {
        "emoji": "🧪",
        "name": "патогена",
        "growth": 2.0,
        "command": "++патоген",
    },
}

COMMAND_TO_FIELD = {
    params["command"]: field for field, params in UPGRADE_PARAMS.items()
}


def calc_cost(field: str, level: int) -> int:
    """
    Стоимость апгрейда поля `field` с уровня `level` до `level+1`,
    по формуле: (level+1)**growth.
    """
    growth = UPGRADE_PARAMS[field]["growth"]
    price = (level + 1) ** growth
    return int(round(price))


def calc_total_cost(field: str, level: int, amount: int) -> int:
    """Общая стоимость `amount` апгрейдов подряд."""
    total = 0
    for i in range(amount):
        total += calc_cost(field, level + i)
    return total


def calc_max_purchase(field: str, level: int, available: float, limit: int = 100) -> tuple[int, int]:
    """Максимум уровней и их цена при лимите и доступных ресурсах."""
    bought = 0
    spent = 0
    while bought < limit:
        cost = calc_cost(field, level + bought)
        if spent + cost > available:
            break
        spent += cost
        bought += 1
    return bought, spent


router = Router()

@router.callback_query(F.data.startswith("upgrade:"))
async def upgrade_skill(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        _, field, owner = callback.data.split(":", 2)
    except ValueError:
        return await callback.answer("Неизвестный параметр", show_alert=True)
    if int(owner) != user_id:
        return await callback.answer("не шали, шалунишка", show_alert=True)

    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await callback.answer("Сначала отправьте /start", show_alert=True)

    lab    = await get_lab_cached(player)
    skills = await get_skill_cached(lab)
    params = UPGRADE_PARAMS.get(field)
    if not params:
        return await callback.answer("Неизвестный параметр", show_alert=True)

    current = getattr(skills, field, 0) if field != "pathogen" else lab.max_pathogens
    if field == "qualification" and current >= 60:
        return await callback.answer("Достигнут максимальный уровень", show_alert=True)

    cost = calc_cost(field, current)
    text = (
        f"<b>{params['emoji']} Прокачка {params['name']} на 1 ур (до {current+1})\n"
        f"🧬 Цена: {short_number(cost)} био-ресурсов</b>\n\n"
        f"<b><i>Команда: \"</i></b>"
        f"<code>{params['command']} {current+1}</code>"
        f"<b><i>\"</i></b>"
    )
    await callback.message.answer(text, reply_markup=confirm_keyboard(field, user_id))
    await callback.answer()

@router.callback_query(F.data.startswith("confirm:"))
async def confirm_upgrade(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        _, field, owner = callback.data.split(":", 2)
    except ValueError:
        return await callback.answer("Неизвестный параметр", show_alert=True)
    if int(owner) != user_id:
        return await callback.answer("не шали, шалунишка", show_alert=True)

    try:
        player = await get_player_cached(user_id)
    except DoesNotExist:
        return await callback.answer("Сначала отправьте /start", show_alert=True)

    lab    = await get_lab_cached(player)
    skills = await get_skill_cached(lab)
    stats  = await get_stats_cached(lab)
    params = UPGRADE_PARAMS[field]

    current = getattr(skills, field, 0) if field != "pathogen" else lab.max_pathogens
    if field == "qualification" and current >= 60:
        return await callback.answer("Достигнут максимальный уровень", show_alert=True)

    cost = calc_cost(field, current)
    if stats.bio_resource < cost:
        return await callback.answer("Недостаточно био-ресурсов", show_alert=True)
    stats.bio_resource -= cost
    await stats.save()

    if field == "pathogen":
        old = lab.max_pathogens
        lab.max_pathogens += 1
        lab.free_pathogens += 1
        await lab.save()
    else:
        old = getattr(skills, field, 0)
        setattr(skills, field, old+1)
        await skills.save()
        if field == "qualification":
            await process_pathogens(lab, skills)

    await callback.message.edit_text(
        f"{params['emoji']} Усиление {params['name']} на {old} ур (до {old+1}) выполнено\n"
        f"🎉 Потрачено: 🧬 {short_number(cost)} био-ресурсов",
        reply_markup=hide_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "hide")
async def hide_message(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.message(F.text.regexp(r'^[/\.]?\+\+'))
async def upgrade_by_command(message: types.Message):
    text    = message.text.lstrip('./').strip()
    parts   = text.split(maxsplit=1)
    command = parts[0].lower()
    arg     = parts[1] if len(parts)>1 else '1'

    field = COMMAND_TO_FIELD.get(command)
    if not field:
        return

    try:
        player = await get_player_cached(message.from_user.id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start")

    lab    = await get_lab_cached(player)
    skills = await get_skill_cached(lab)
    stats  = await get_stats_cached(lab)

    current = getattr(skills, field, 0) if field!='pathogen' else lab.max_pathogens

    if arg.lower() == 'макс':
        limit = 60-current if field=='qualification' else 100
        amount, cost = calc_max_purchase(field, current, stats.bio_resource, limit=limit)
        if amount == 0:
            return await message.answer("Недостаточно био-ресурсов")
    else:
        try:
            amount = int(arg)
        except ValueError:
            return await message.answer("Укажите число или 'макс'")
        limit = 60-current if field=='qualification' else 100
        amount = max(1, min(limit, amount))
        cost = calc_total_cost(field, current, amount)
        if cost > stats.bio_resource:
            return await message.answer("Недостаточно био-ресурсов")

    stats.bio_resource -= cost
    await stats.save()

    if field == 'pathogen':
        lab.max_pathogens += amount
        lab.free_pathogens += amount
        new_level = lab.max_pathogens
        await lab.save()
    else:
        setattr(skills, field, current+amount)
        new_level = current+amount
        await skills.save()
        if field=='qualification':
            await process_pathogens(lab, skills)

    params = UPGRADE_PARAMS[field]
    await message.answer(
        f"{params['emoji']}<b> Усиление {params['name']} на {amount} (до {new_level}) выполнено\n"
        f"🎉 Потрачено: 🧬 {short_number(cost)} био-ресурсов</b>"
    )
