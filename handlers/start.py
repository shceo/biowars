# handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart
from models.player import Player
from datetime import datetime, timedelta

from models.laboratory import Laboratory
from models.skill import Skill
from models.statistics import Statistics

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Регистрируем игрока, если надо
    player, created = await Player.get_or_create(
        telegram_id=message.from_user.id,
        defaults={"full_name": message.from_user.full_name},
    )
    if created:
        # Создаём лабораторию с начальными данными + связанные записи
        lab = await Laboratory.create(
            player=player,
            free_pathogens=10,
            max_pathogens=10,
            next_pathogen_at=datetime.utcnow() + timedelta(minutes=60),
        )
        await Skill.create(
            lab=lab,
            infectivity=1,
            immunity=1,
            lethality=1,
            safety=1,
            qualification=1,
        )
        await Statistics.create(lab=lab)

    # Приветственный текст
    welcome_text = (
        "<b>Добро пожаловать в shit wars! 🦠</b>\n\n"
        "<b>📟 Команды:</b>\n"
        "<blockquote><b>🔸 soon</b></blockquote>\n\n"
        "<b>💬 Наш чат:</b>\n"
        "<blockquote><b>🔸 soon</b></blockquote>\n\n"
        "<b><i>📛 Играя в игру вы соглашаетесь с правилами.</i></b>"
    )
    await message.answer(welcome_text)
