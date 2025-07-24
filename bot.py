# bot.py
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from middlewares.cooldown import CooldownMiddleware
from tortoise import Tortoise

from config import settings  # config.py должно использовать pydantic-settings

async def init_db():
    await Tortoise.init(
        db_url=settings.database_url,
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()

async def main():
    # Создаём Bot с HTML‑парсингом по умолчанию
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware.register(CooldownMiddleware(1.0))

    # Регистрируем все роутеры
    from handlers.start import router as start_router
    dp.include_router(start_router)
    from handlers.lab.status import router as lab_status_router
    dp.include_router(lab_status_router)
    from handlers.lab.skills import router as lab_skills_router
    dp.include_router(lab_skills_router)
    from handlers.lab.pathogen_name import router as pathogen_name_router
    dp.include_router(pathogen_name_router)
    from handlers.admin import router as admin_router
    dp.include_router(admin_router)
    from handlers.infect import router as infect_router
    dp.include_router(infect_router)

    # TODO: подключите сюда остальные роутеры, например:
    # from handlers.lab.status import router as lab_status_router
    # dp.include_router(lab_status_router)

    # Инициализируем базу
    await init_db()

    # Стартуем polling и корректно закрываем сессию
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
