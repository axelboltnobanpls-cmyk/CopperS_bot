import asyncio

from bot import bot as main_bot, dp as main_dp
from admin_panel import bot as admin_bot, dp as admin_dp

async def main():
    print("🚀 Запуск основного бота...")
    print("🔐 Запуск админ-панели...")
    await asyncio.gather(
        main_dp.start_polling(main_bot),
        admin_dp.start_polling(admin_bot),
    )

if __name__ == "__main__":
    asyncio.run(main())