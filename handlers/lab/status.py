# handlers/lab/status.py

import re
from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from tortoise.exceptions import DoesNotExist

from models.player import Player
from models.laboratory import Laboratory
from models.skill import Skill
from models.statistics import Statistics
from models.pathogen import Pathogen

router = Router()

@router.message(
    # ловим "биолаб", "бл" или "лаб" с любым префиксом (/ . или без)
    F.text.regexp(r'^[/.]?(?:биолаб|бл|лаб)$', flags=re.IGNORECASE)
)
async def cmd_lab_status(message: types.Message):
    user_id = message.from_user.id

    # 1) Проверка, что игрок есть
    try:
        player = await Player.get(telegram_id=user_id)
    except DoesNotExist:
        return await message.answer("Сначала отправьте /start, чтобы зарегистрироваться.")

    # 2) Загружаем лабораторию + связи
    lab = await Laboratory.get(player=player).prefetch_related("stats", "corporation")
    stats = await lab.stats
    skills = await Skill.get(lab=lab)

    # 3) Берём последний созданный патоген (если был)
    pathogen = await Pathogen.filter(lab=lab).order_by("-created_at").first()
    pathogen_name = pathogen.name if pathogen else None

    # 4) Данные корпорации
    if lab.corporation:
        corp_name  = lab.corporation.name
        corp_tg_id = lab.corporation.tg_id
    else:
        corp_name  = "—"
        corp_tg_id = user_id

    # 5) Активность
    blocks = "▪️" * max(1, lab.activity // 20)

    # 6) До нового патогена
    if lab.next_pathogen_at:
        delta = lab.next_pathogen_at - datetime.utcnow()
        secs  = max(0, int(delta.total_seconds()))
    else:
        secs = 0

    # 7) Безопасное вычисление процентов
    if stats.operations_total > 0:
        ops_pct       = f"{stats.operations_done / stats.operations_total:.0%}"
        blocked_pct   = f"{stats.operations_blocked / stats.operations_total:.0%}"
    else:
        ops_pct       = "0%"
        blocked_pct   = "0%"

    # 8) HTML‑текст
    text = (
        f"<b>🔬 Лаборатория игрока:</b> "
        f"<a href=\"tg://openmessage?user_id={user_id}\">[🎪] {message.from_user.full_name}</a>\n"
        f"🏢 В составе корпорации: "
        f"«<a href=\"tg://openmessage?user_id={corp_tg_id}\">{corp_name}</a>»\n\n"

        f"<b>🔋 Активность: [{blocks}] {lab.activity}%</b>\n"
        f"<blockquote>Майнинг +{lab.mining_bonus}% 💎 | Премия +{lab.premium_bonus}% 🧬</blockquote>\n"
        f"🏷 Имя патогена — <code>{pathogen_name or 'None'}</code>;\n"
        f"🧪 Свободных патогенов: {lab.free_pathogens} из {lab.max_pathogens} "
        f"(<code>+{lab.max_pathogens - lab.free_pathogens}</code>)\n\n"

        f"<b>🌎 Навыки:</b>\n"
        f"<blockquote>🦠 Заразность: {skills.infectivity} ур.\n"
        f"🛡 Иммунитет: {skills.immunity} ур.\n"
        f"☠️ Летальность: {skills.lethality} ур.\n"
        f"🕵🏻‍♂️ Безопасность: {skills.safety} ур.\n"
        f"👩🏻‍🔬 Квалификация: {skills.qualification} ур.\n"
        f"⏱️ До нового патогена: {secs} сек.</blockquote>\n\n"

        f"<b>📊 Статистика:</b>\n"
        f"<blockquote>☢️ Био‑опыт: {stats.bio_experience}\n"
        f"🧬 Био‑ресурс: {stats.bio_resource}\n"
        f"😷 Спецопераций: {stats.operations_done}/{stats.operations_total} ({ops_pct})\n"
        f"🥽 Предотвращены: {stats.operations_blocked}/{stats.operations_total} ({blocked_pct})</blockquote>\n"

        f"<b>🤒 Заражённых: {stats.infected_count}\n"
        f"😨 Своих болезней: {stats.own_diseases}</b>"
    )

    await message.answer(text)
