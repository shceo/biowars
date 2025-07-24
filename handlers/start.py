# handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart
from services.lab_service import register_player_if_needed

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Регистрируем игрока и лабораторию при первом запуске
    await register_player_if_needed(
        message.from_user.id,
        message.from_user.full_name,
    )

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
