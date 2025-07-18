from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def lab_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # First row
    builder.button(text="🧪", callback_data="upgrade:pathogen")
    builder.button(text="👩\u200d🔬", callback_data="upgrade:qualification")
    builder.button(text="🦠", callback_data="upgrade:infectivity")
    # Second row
    builder.button(text="🛡", callback_data="upgrade:immunity")
    builder.button(text="💀", callback_data="upgrade:lethality")
    builder.button(text="🕵", callback_data="upgrade:safety")
    builder.adjust(3, 3)
    return builder.as_markup()
