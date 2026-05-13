import json
import os
import sqlite3
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram import FSMContext

# ======================== ПУТИ ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(BASE_DIR, "keys.json")
DATABASE_FILE = os.path.join(BASE_DIR, "users.db")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# ======================== НАСТРОЙКИ ========================
BOT_TOKEN = os.environ.get("ADMIN_TOKEN", "8601852006:AAFZEsIP6WgbfwDbbW4LShK7oytq6E8neOY")
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

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# ======================== ФУНКЦИИ ========================
def load_keys() -> list:
    if not os.path.exists(KEYS_FILE):
        return []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("keys", [])
    except Exception:
        return []


def save_keys(keys: list):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump({"keys": keys}, f, ensure_ascii=False, indent=2)


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


def get_all_users() -> list:
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, received_key FROM users")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def delete_user(user_id: int) -> bool:
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    except Exception:
        return False


def delete_all_users() -> int:
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected
    except Exception:
        return 0


def reset_keys() -> bool:
    try:
        save_keys([])
        return True
    except Exception:
        return False


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def export_keys_to_text() -> str:
    keys = load_keys()
    if not keys:
        return "📭 Ключей нет в базе."
    text = "🔑 <b>Все ключи:</b>\n\n"
    for i, k in enumerate(keys, 1):
        text += f"<code>{k}</code>\n"
    return text


def export_users_to_text() -> str:
    users = get_all_users()
    if not users:
        return "👤 Пользователей нет в базе."
    text = "👥 <b>Все пользователи:</b>\n\n"
    for uid, uname, fname, key in users:
        u = f"@{uname}" if uname and uname != "N/A" else fname
        k = key if key and key != "N/A" else "—"
        text += f"👤 {u} | <code>{uid}</code> | Ключ: <code>{k}</code>\n"
    return text


# ======================== СОСТОЯНИЯ FSM ========================
class AdminStates:
    waiting_add_keys = "waiting_add_keys"
    waiting_del_key = "waiting_del_key"
    waiting_broadcast = "waiting_broadcast"


# ======================== ГЛАВНОЕ МЕНЮ ========================
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Добавить ключи", callback_data="admin_add_keys")],
        [InlineKeyboardButton(text="🗑️ Удалить ключ", callback_data="admin_del_key")],
        [InlineKeyboardButton(text="📋 Список ключей", callback_data="admin_list_keys")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔄 Сброс ключей", callback_data="admin_reset_keys")],
        [InlineKeyboardButton(text="🗑️ Сброс пользователей", callback_data="admin_reset_users")],
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_main_menu")]
    ])


# ======================== ОБРАБОТЧИКИ ========================

# --- /admin — вход в панель ---
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой панели.")
        return

    await state.clear()
    await message.answer(
        "🔐 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


# --- Callback: Главное меню ---
@router.callback_query(F.data == "admin_main_menu")
async def admin_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


# --- Callback: Добавить ключи ---
@router.callback_query(F.data == "admin_add_keys")
async def admin_add_keys_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_add_keys)
    await callback.message.edit_text(
        "📝 <b>Добавить ключи</b>\n\n"
        "Отправьте ключи — каждый с новой строка:\n\n"
        "<code>XXXX-XXXX-XXXX\nYYYY-YYYY-YYYY\nZZZZ-ZZZZ-ZZZZ</code>\n\n"
        "Или одной строкой через пробел:\n"
        "<code>XXXX-XXXX-XXXX YYYY-YYYY-YYYY</code>",
        reply_markup=get_back_keyboard()
    )


@router.message(AdminStates.waiting_add_keys)
async def admin_add_keys_process(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Введите ключи!")
        return

    # Поддержка и построчный ввод, и через пробел
    if "\n" in text:
        new_keys = [k.strip() for k in text.split("\n") if k.strip()]
    else:
        new_keys = [k.strip() for k in text.split() if k.strip()]

    if not new_keys:
        await message.answer("❌ Ключи не распознаны.")
        return

    existing = load_keys()
    existing.extend(new_keys)
    save_keys(existing)

    await state.clear()
    await message.answer(
        f"✅ Добавлено <b>{len(new_keys)}</b> ключей.\n"
        f"📊 Всего в базе: <b>{len(existing)}</b>",
        reply_markup=get_main_menu_keyboard()
    )


# --- Callback: Удалить ключ ---
@router.callback_query(F.data == "admin_del_key")
async def admin_del_key_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_del_key)
    await callback.message.edit_text(
        "🗑️ <b>Удалить ключ</b>\n\n"
        "Введите ключ, который хотите удалить:\n\n"
        "<code>XXXX-XXXX-XXXX</code>",
        reply_markup=get_back_keyboard()
    )


@router.message(AdminStates.waiting_del_key)
async def admin_del_key_process(message: Message, state: FSMContext):
    key_to_del = message.text.strip()
    keys = load_keys()

    if key_to_del in keys:
        keys.remove(key_to_del)
        save_keys(keys)
        await state.clear()
        await message.answer(
            f"✅ Ключ <code>{key_to_del}</code> удалён.\n"
            f"📊 Осталось: <b>{len(keys)}</b>",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ключ <code>{key_to_del}</code> не найден в базе.",
            reply_markup=get_back_keyboard()
        )


# --- Callback: Список ключей ---
@router.callback_query(F.data == "admin_list_keys")
async def admin_list_keys(callback: CallbackQuery):
    keys = load_keys()
    if not keys:
        await callback.answer("📭 Ключей нет!", show_alert=True)
        return

    text = "🔑 <b>Ключи в базе:</b>\n\n"
    for i, k in enumerate(keys, 1):
        text += f"{i}. <code>{k}</code>\n"

    if len(text) > 4000:
        parts = [text[j:j+4000] for j in range(0, len(text), 4000)]
        for part in parts:
            await callback.message.answer(part)
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard())


# --- Callback: Статистика ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    keys = load_keys()
    total_users = get_total_users()

    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"🔑 Ключей в базе: <b>{len(keys)}</b>\n"
        f"👤 Пользователей получило ключ: <b>{total_users}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())


# --- Callback: Пользователи ---
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    users = get_all_users()
    if not users:
        await callback.message.edit_text(
            "👤 Пока нет пользователей в базе.",
            reply_markup=get_back_keyboard()
        )
        return

    text = f"👥 <b>Пользователи ({len(users)} чел.):</b>\n\n"
    for uid, uname, fname, key in users[:50]:  # Показываем первых 50
        u = f"@{uname}" if uname and uname != "N/A" else (fname or "N/A")
        k = f"<code>{key}</code>" if key and key != "N/A" else "—"
        text += f"👤 {u} — {k}\n"

    if len(users) > 50:
        text += f"\n... и ещё {len(users) - 50} чел."

    if len(text) > 4000:
        await callback.message.edit_text(
            "👥 Список пользователей очень большой. Экспортирую отдельными сообщениями..."
        )
        for part in [text[j:j+4000] for j in range(0, len(text), 4000)]:
            await callback.message.answer(part)
    else:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard())


# --- Callback: Сброс ключей ---
@router.callback_query(F.data == "admin_reset_keys")
async def admin_reset_keys(callback: CallbackQuery):
    keys = load_keys()
    if reset_keys():
        await callback.message.edit_text(
            f"🔄 <b>Ключи сброшены!</b>\n\nБыло удалено: <b>{len(keys)}</b> ключей.\n"
            "База `keys.json` теперь пуста.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка при сбросе ключей!", show_alert=True)


# --- Callback: Сброс пользователей ---
@router.callback_query(F.data == "admin_reset_users")
async def admin_reset_users(callback: CallbackQuery):
    count = delete_all_users()
    await callback.message.edit_text(
        f"🔄 <b>Пользователи сброшены!</b>\n\nУдалено записей: <b>{count}</b>.",
        reply_markup=get_main_menu_keyboard()
    )


# --- Callback: Рассылка ---
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Введите текст сообщения, которое отправится всем пользователям:\n\n"
        "Например:\n"
        "<code>🔔 Обновление! Скоро новые ключи!</code>",
        reply_markup=get_back_keyboard()
    )


@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast_process(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Введите текст сообщения!")
        return

    users = get_all_users()
    if not users:
        await state.clear()
        await message.answer("👤 Нет пользователей для рассылки.")
        return

    success = 0
    failed = 0

    for uid, _, _, _ in users:
        try:
            await bot.send_message(
                chat_id=uid,
                text=f"📢 <b>Сообщение от администрации:</b>\n\n{text}",
                parse_mode=ParseMode.HTML
            )
            success += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Отправлено: <b>{success}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>\n"
        f"👤 Всего пользователей: <b>{len(users)}</b>",
        reply_markup=get_main_menu_keyboard()
    )


# --- Catch-all ---
@router.message()
async def catch_all(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Команда не найдена. Введите /admin для входа в панель.")


@router.callback_query()
async def catch_all_callback(callback: CallbackQuery):
    await callback.answer("Неизвестное действие", show_alert=True)


# ======================== ЗАПУСК ========================
async def main():
    logger.info("=" * 50)
    logger.info("🔐 АДМИН-ПАНЕЛЬ ЗАПУЩЕНА")
    logger.info(f"👥 Всего пользователей: {get_total_users()}")
    logger.info(f"🔑 Ключей в базе: {len(load_keys())}")
    logger.info("=" * 50)

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
