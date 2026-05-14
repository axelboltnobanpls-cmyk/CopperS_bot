import asyncio

# Импортируем всё что нужно
from bot import bot as main_bot, dp as main_dp, router as main_router
from bot import init_db, ensure_keys_file

from admin_panel import bot as admin_bot, dp as admin_dp, router as admin_router

async def main():
    # Инициализация основного бота
    init_db()
    ensure_keys_file()

    # Подключаем роутеры РАНЬШЕ запуска polling
    main_dp.include_router(main_router)
    admin_dp.include_router(admin_router)

    print("🚀 Запуск основного бота...")
    print("🔐 Запуск админ-панели...")

    await asyncio.gather(
        main_dp.start_polling(main_bot),
        admin_dp.start_polling(admin_bot),
    )

if __name__ == "__main__":
    asyncio.run(main())