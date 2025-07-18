from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def lab_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # First row
    builder.button(text="🧪", callback_data=f"upgrade:pathogen:{owner_id}")
    builder.button(text="👩\u200d🔬", callback_data=f"upgrade:qualification:{owner_id}")
    builder.button(text="🦠", callback_data=f"upgrade:infectivity:{owner_id}")
    # Second row
    builder.button(text="🛡", callback_data=f"upgrade:immunity:{owner_id}")
    builder.button(text="💀", callback_data=f"upgrade:lethality:{owner_id}")
    builder.button(text="🕵", callback_data=f"upgrade:safety:{owner_id}")
    builder.adjust(3, 3)
    return builder.as_markup()


def confirm_keyboard(field: str, owner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Улучшить", callback_data=f"confirm:{field}:{owner_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def hide_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Скрыть", callback_data="hide")
    builder.adjust(1)
    return builder.as_markup()
