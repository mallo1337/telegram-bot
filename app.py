import asyncio
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database

# --- Переменные окружения ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден!")

# --- База данных ---
db = Database()

# ---------- ОБРАБОТЧИКИ БОТА ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_player(
        user_id=user.id,
        username=user.username or "NoUsername",
        first_name=user.first_name
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск 2x2", callback_data="search_2x2")],
        [InlineKeyboardButton("🔍 Поиск 5x5", callback_data="search_5x5")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "🎮 Добро пожаловать в соревновательный бот!\n"
        "Выбери режим:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == "search_2x2":
        if await db.is_muted(user_id):
            await query.edit_message_text(
                "❌ Ты в муте! Подожди 5 минут.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
            return
        
        lobby_id = await db.add_to_lobby_2x2(user_id)
        
        if await db.is_lobby_full_2x2(lobby_id):
            await query.edit_message_text("✅ Лобби заполнено! Ожидай начала матча...")
        else:
            await query.edit_message_text(
                "🔍 Ищешь соперника для 2x2...\nОжидай, когда лобби заполнится.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Отменить поиск", callback_data=f"cancel_{lobby_id}")]
                ])
            )
    
    elif query.data == "search_5x5":
        await query.edit_message_text(
            "🚧 Режим 5х5 в разработке!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif query.data == "profile":
        player = await db.get_player(user_id)
        if player:
            await query.edit_message_text(
                f"👤 Твой профиль:\n"
                f"ID: {player['user_id']}\n"
                f"Имя: {player['first_name']}\n"
                f"Ник: @{player['username']}\n"
                f"Зарегистрирован: {player['registered_at']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
    
    elif query.data.startswith("cancel_"):
        lobby_id = int(query.data.split("_")[1])
        await db.remove_from_lobby_2x2(user_id, lobby_id)
        await query.edit_message_text(
            "🚫 Ты отменил поиск.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск 2x2", callback_data="search_2x2")],
            [InlineKeyboardButton("🔍 Поиск 5x5", callback_data="search_5x5")],
            [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
        ]
        await query.edit_message_text(
            "🎮 Главное меню:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------- ФУНКЦИЯ ЗАПУСКА БОТА ----------
async def run_bot():
    await db.connect()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Бот запущен и готов к работе!")
    await app.run_polling()

# ---------- ВЕБ-СЕРВЕР ДЛЯ RENDER ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)

# ---------- ГЛАВНЫЙ ЗАПУСК ----------
if __name__ == "__main__":
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запускаем бота в основном потоке
    try:
        asyncio.run(run_bot())
    except RuntimeError as e:
        # Если цикл уже запущен, используем get_running_loop
        if "already running" in str(e):
            loop = asyncio.get_running_loop()
            loop.create_task(run_bot())
            loop.run_forever()import asyncio
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database

# --- Переменные окружения ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден!")

# --- База данных ---
db = Database()

# ---------- ОБРАБОТЧИКИ БОТА ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_player(
        user_id=user.id,
        username=user.username or "NoUsername",
        first_name=user.first_name
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск 2x2", callback_data="search_2x2")],
        [InlineKeyboardButton("🔍 Поиск 5x5", callback_data="search_5x5")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "🎮 Добро пожаловать в соревновательный бот!\n"
        "Выбери режим:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == "search_2x2":
        if await db.is_muted(user_id):
            await query.edit_message_text(
                "❌ Ты в муте! Подожди 5 минут.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
            return
        
        lobby_id = await db.add_to_lobby_2x2(user_id)
        
        if await db.is_lobby_full_2x2(lobby_id):
            await query.edit_message_text("✅ Лобби заполнено! Ожидай начала матча...")
        else:
            await query.edit_message_text(
                "🔍 Ищешь соперника для 2x2...\nОжидай, когда лобби заполнится.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Отменить поиск", callback_data=f"cancel_{lobby_id}")]
                ])
            )
    
    elif query.data == "search_5x5":
        await query.edit_message_text(
            "🚧 Режим 5х5 в разработке!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif query.data == "profile":
        player = await db.get_player(user_id)
        if player:
            await query.edit_message_text(
                f"👤 Твой профиль:\n"
                f"ID: {player['user_id']}\n"
                f"Имя: {player['first_name']}\n"
                f"Ник: @{player['username']}\n"
                f"Зарегистрирован: {player['registered_at']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
    
    elif query.data.startswith("cancel_"):
        lobby_id = int(query.data.split("_")[1])
        await db.remove_from_lobby_2x2(user_id, lobby_id)
        await query.edit_message_text(
            "🚫 Ты отменил поиск.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск 2x2", callback_data="search_2x2")],
            [InlineKeyboardButton("🔍 Поиск 5x5", callback_data="search_5x5")],
            [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
        ]
        await query.edit_message_text(
            "🎮 Главное меню:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------- ФУНКЦИЯ ЗАПУСКА БОТА ----------
async def run_bot():
    await db.connect()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Бот запущен и готов к работе!")
    await app.run_polling()

# ---------- ВЕБ-СЕРВЕР ДЛЯ RENDER ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)

# ---------- ГЛАВНЫЙ ЗАПУСК ----------
if __name__ == "__main__":
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запускаем бота в основном потоке
    asyncio.run(run_bot())
