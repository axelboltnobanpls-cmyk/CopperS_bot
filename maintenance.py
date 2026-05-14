import json
import os
import sqlite3
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ======================== ПУТИ ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(BASE_DIR, "keys.json")
DATABASE_FILE = os.path.join(BASE_DIR, "users.db")

# ======================== НАСТРОЙКИ ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8675981214:AAHkjjcFAhSTisGVF15O7MR3Be7hUhVyasg")
CHANNEL_USERNAME = "@copperS_shop"
CHANNEL_LINK = "https://t.me/copperS_shop"
GGSEL_LINK = "https://ggsel.net/sellers/132805517"
ADMIN_IDS = [7079908197, 6797520714]
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()


# ======================== ЗАГРУЗКА КЛЮЧЕЙ (ТОЛЬКО ЧТЕНИЕ) ========================
def load_keys() -> list:
    if not os.path.exists(KEYS_FILE):
        return []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("keys", [])
    except Exception:
        return []


def get_keys_count() -> int:
    return len(load_keys())


def get_total_users() -> int:
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception:
        return 0


# ======================== ОБРАБОТЧИКИ ========================

# --- /start в режиме техобслуживания ---
@router.message(CommandStart())
async def maintenance_start(message: Message):
    uid = message.from_user.id
    logger.info(f"👋 /start от {uid} (РЕЖИМ ТЕХОБСЛУЖИВАНИЯ)")

    keys_count = get_keys_count()

    await message.answer(
        "🔧 <b>Технический перерыв</b>\n\n"
        "Ведутся технические работы. Мы улучшаем бота, исправляем баги "
        "и добавляем новые функции.\n"
        "Приносим извинения за неудобства! 🤗\n\n"
        f"🔑 Ключей в базе: <b>{keys_count}</b>\n\n"
        f"📢 Подпишитесь, чтобы не пропустить запуск:\n"
        f"<a href=\"{CHANNEL_LINK}\">copperS_shop</a>",
        disable_web_page_preview=True
    )


# --- Ответ на ЛЮБОЕ текстовое сообщение ---
@router.message()
async def maintenance_message(message: Message):
    uid = message.from_user.id
    logger.info(f"📩 Сообщение от {uid}: {message.text}")

    await message.answer(
        "🔧 <b>Технический перерыв</b>\n\n"
        "Мы улучшаем бота и исправляем баги.\n"
        "Приносим извинения за неудобства! 🤗\n\n"
        f"📢 Следите за новостями: <a href=\"{CHANNEL_LINK}\">copperS_shop</a>",
        disable_web_page_preview=True
    )


# --- Админ: статистика ---
@router.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет прав.")
        return

    keys = load_keys()
    total_users = get_total_users()

    text = (
        f"📊 <b>Статистика (режим обслуживания):</b>\n\n"
        f"🔑 Ключей осталось: <b>{len(keys)}</b>\n"
        f"👤 Ключей выдано: <b>{total_users}</b>"
    )
    await message.answer(text)


# --- Админ: список ключей ---
@router.message(Command("listkeys"))
async def admin_list_keys(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    keys = load_keys()
    if not keys:
        await message.answer("📭 Ключей нет в базе.")
        return

    text = "🔑 <b>Ключи в базе:</b>\n\n"
    for i, k in enumerate(keys, 1):
        text += f"{i}. <code>{k}</code>\n"

    if len(text) > 4000:
        for part in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
            await message.answer(part)
    else:
        await message.answer(text)


# --- Админ: добавить ключи (в режиме обслуживания можно загрузить) ---
@router.message(Command("addkey"))
async def admin_add_key(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет прав.")
        return

    text = message.text.replace("/addkey", "").strip()
    if not text:
        await message.answer("📝 <code>/addkey\nKEY-1\nKEY-2\nKEY-3</code>")
        return

    new_keys = [k.strip() for k in text.split("\n") if k.strip()]
    if not new_keys:
        await message.answer("❌ Ключи не найдены.")
        return

    keys = load_keys()
    keys.extend(new_keys)

    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump({"keys": keys}, f, ensure_ascii=False, indent=2)

    logger.info(f"🗝️ Админ {message.from_user.id} добавил {len(new_keys)} ключей")
    await message.answer(
        f"✅ Добавлено <b>{len(new_keys)}</b> ключей.\n"
        f"📊 Всего в базе: <b>{len(keys)}</b>"
    )


# --- Админ: удалить ключ ---
@router.message(Command("delkey"))
async def admin_del_key(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет прав.")
        return

    key_to_del = message.text.replace("/delkey", "").strip()
    if not key_to_del:
        await message.answer("Использование: <code>/delkey XXXX-XXXX-XXXX</code>")
        return

    keys = load_keys()
    if key_to_del in keys:
        keys.remove(key_to_del)
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump({"keys": keys}, f, ensure_ascii=False, indent=2)
        await message.answer(f"✅ Ключ <code>{key_to_del}</code> удалён.")
    else:
        await message.answer(f"❌ Ключ не найден.")


# --- Catch-all ---
@router.callback_query()
async def catch_all_callback(callback: F):
    await callback.answer("🔧 Технический перерыв. Скоро запустимся!", show_alert=True)


# ======================== ЗАПУСК ========================
async def main():
    logger.info("=" * 50)
    logger.info("🔧 БОТ В РЕЖИМЕ ТЕХОБСЛУЖИВАНИЯ")
    logger.info(f"📢 Канал: {CHANNEL_USERNAME}")
    logger.info(f"🔑 Ключей в базе: {get_keys_count()}")
    logger.info("=" * 50)

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())