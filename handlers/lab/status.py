# handlers/lab/status.py

import re
from datetime import datetime, timezone

from aiogram import Router, types, F
from aiogram.filters import Command
from services.lab_service import (
    get_player_cached,
    get_lab_cached,
    get_skill_cached,
    get_stats_cached,
    process_pathogens,
    register_player_if_needed,
)
from utils.formatting import short_number

from keyboards.lab_kb import lab_keyboard

router = Router()

@router.message(
    # ловим "биолаб", "бл" или "лаб" с любым префиксом (/ . или без)
    F.text.regexp(r'^[/.]?(?:биолаб|бл|лаб)$', flags=re.IGNORECASE)
)
async def cmd_lab_status(message: types.Message):
    user_id = message.from_user.id

    # 1) Проверка/создание игрока и лаборатории
    player = await register_player_if_needed(
        user_id,
        message.from_user.full_name,
    )

    # 2) Загружаем лабораторию + связи
    lab = await get_lab_cached(player)
    stats = await get_stats_cached(lab)
    skills = await get_skill_cached(lab)

    # update pathogen production based on current time
    await process_pathogens(lab, skills)

    # 3) Имя патогена, заданное игроком
    pathogen_name = lab.pathogen_name

    # 4) Данные корпорации
    if lab.corporation:
        corp_name = lab.corporation.name
        corp_tg_id = lab.corporation.tg_id
        corp_line = (
            f"🏢 В составе корпорации: "
            f"«<a href=\"tg://openmessage?user_id={corp_tg_id}\">{corp_name}</a>»\n\n"
        )
    else:
        corp_line = ""

    # 5) Активность
    blocks = "▫️▫️▫️▫️▫️" * max(1, lab.activity // 20)

    # 6) До нового патогена
    if lab.next_pathogen_at:
        delta = lab.next_pathogen_at - datetime.now(timezone.utc)
        mins = max(0, int(delta.total_seconds() // 60))
    else:
        mins = 0

    # 7) Безопасное вычисление процентов
    if stats.operations_total > 0:
        ops_pct       = f"{stats.operations_done / stats.operations_total:.0%}"
        blocked_pct   = f"{stats.operations_blocked / stats.operations_total:.0%}"
    else:
        ops_pct = "0%"
        blocked_pct = "0%"

    # 8) HTML‑текст
    text = (
        f"<b>🔬 Лаборатория игрока:</b> "
        f"<a href=\"tg://openmessage?user_id={user_id}\">{message.from_user.full_name}</a>\n"
        f"{corp_line}\n"

        f"<b>🪫 Активность: [{blocks}] {lab.activity}%</b>\n"
        f"<blockquote>Премия +{lab.premium_bonus}% 🧬</blockquote>\n" 
        # Майнинг +{lab.mining_bonus}% 💎 | 
        f"🏷 Имя патогена — <code>{pathogen_name or 'None'}</code>;\n"
        f"🧪 Свободных патогенов: {short_number(lab.free_pathogens)} "
        f"из {short_number(lab.max_pathogens)}\n\n"
        # f"(<code>+{short_number(lab.max_pathogens - lab.free_pathogens)}</code>)\n\n"

        f"<b>🌎 Навыки:</b>\n"
        f"<blockquote>🦠 Заразность: {skills.infectivity} ур.\n"
        f"🛡 Иммунитет: {skills.immunity} ур.\n"
        f"☠️ Летальность: {skills.lethality} ур.\n"
        f"🕵🏻‍♂️ Безопасность: {skills.safety} ур.\n"
        f"👩🏻‍🔬 Квалификация: {skills.qualification} ур.\n"
        f"⏱️ До нового патогена: {mins} мин.</blockquote>\n\n"

        f"<b>📊 Статистика:</b>\n"
        f"<blockquote>☢️ Био‑опыт: {short_number(stats.bio_experience)}\n"
        f"🧬 Био‑ресурс: {short_number(stats.bio_resource)}\n"
        f"😷 Спецопераций: {short_number(stats.operations_done)}/{short_number(stats.operations_total)} ({ops_pct})\n"
        f"🥽 Предотвращены: {short_number(stats.operations_blocked)}/{short_number(stats.operations_total)} ({blocked_pct})</blockquote>\n\n"

        f"<b>🤒 Заражённых: {short_number(stats.infected_count)}\n"
        f"😨 Своих болезней: {short_number(stats.own_diseases)}</b>"
    )

    await message.answer(text, reply_markup=lab_keyboard(user_id))
