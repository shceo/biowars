from aiogram import Router, types, F
import re
from services.lab_service import (
    register_player_if_needed,
    get_lab_cached,
    get_stats_cached,
    get_skill_cached,
    process_pathogens,
    cleanup_expired_infections,
)
from utils.formatting import short_number

router = Router()

@router.message(
    F.text.regexp(r'^[/.]?(?:минилаб|млаб|мл)$', flags=re.IGNORECASE)
)
async def cmd_minilab(message: types.Message):
    user_id = message.from_user.id

    player = await register_player_if_needed(
        user_id,
        message.from_user.full_name,
    )

    lab = await get_lab_cached(player)
    stats = await get_stats_cached(lab)
    await cleanup_expired_infections(lab)
    await process_pathogens(lab, await get_skill_cached(lab))

    display_name = lab.lab_name or message.from_user.full_name

    text = (
        f"<b>🔬 Лаборатория:</b> "
        f"<a href=\"tg://openmessage?user_id={user_id}\">{display_name}</a>\n"
        f"<blockquote>🧪 Свободных патогенов: {short_number(lab.free_pathogens)} из {short_number(lab.max_pathogens)}\n"
        f"☢️ Био‑опыт: {short_number(stats.bio_experience)}\n"
        f"🧬 Био‑ресурс: {short_number(stats.bio_resource)}</blockquote>"
    )
    await message.answer(text)
