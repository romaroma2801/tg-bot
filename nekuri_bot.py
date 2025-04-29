from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
from logging.handlers import RotatingFileHandler
with open("/home/roman2801/nekuri_bot/store_full.json", "r", encoding="utf-8") as f:
    stores_data = json.load(f)

import logging
# другие импорты...
import zlib

def get_city_hash(city_name):
    """Преобразует название города в короткий хеш (CRC32)."""
    return hex(zlib.crc32(city_name.encode('utf-8')))[2:]  # Пример: "гродно" → "a5b3c2d1"
log_file = '/home/roman2801/nekuri_log.txt'
handler = RotatingFileHandler(
    log_file,
    maxBytes=2*1024*1024,  # 2 MB (макс размер одного файла)
    backupCount=3,         # Хранить 3 архивных файла
    encoding='utf-8'
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("🚀 Бот запущен")

# Токен бота
TOKEN = '7549154782:AAHfSaSZ6rJYzWtC9x3_Iqa8xUnTGNybT3o'

# Структура с магазинами

# Стартовое сообщение и главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    keyboard = [
        [InlineKeyboardButton("📍 Адреса магазинов", callback_data='addresses'),
         InlineKeyboardButton("📝 Оставить отзыв", callback_data='review')],
        [InlineKeyboardButton("📣 Социальные сети", callback_data='socials'),
         InlineKeyboardButton("📞 Контакты", callback_data='contacts')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
    "👋 Добро пожаловать в бот от магазина *NEKURI.BY!*\n\n"
    "Здесь вы можете:\n\n"
    "📍 Посмотреть локации наших магазинов в вашем городе\n"
    "📝 Оставить отзыв — его сразу увидит наш менеджер\n"
    "🌐 Перейти на официальные страницы в соцсетях\n"
    "📞 Получить контакты нашей службы поддержки\n\n"
    "👇 Выберите нужный раздел ниже:"
)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(region, callback_data=f"region_{region}")]
        for region in stores_data.keys()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите область:", reply_markup=reply_markup)


async def show_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    region = query.data.replace("region_", "")
    context.user_data['region'] = region

    keyboard = [
        [InlineKeyboardButton(city, callback_data=f"city_{city}")]
        for city in stores_data[region].keys()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='addresses')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Вы выбрали: {region}\nТеперь выберите город:", reply_markup=reply_markup)


async def show_stores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    city = query.data.replace("city_", "")
    region = context.user_data.get("region")
    context.user_data["city"] = city

    stores = stores_data[region][city]

    keyboard = [
        [InlineKeyboardButton(store["name"], callback_data=f"store_{i}")]
        for i, store in enumerate(stores)
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"region_{region}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"<b>{region}</b> → <b>{city}</b>\nВыберите магазин:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )
from datetime import datetime, timedelta
import os

FEEDBACK_LOG_PATH = "/home/roman2801/nekuri_bot/feedback_log.json"

def load_feedback_log():
    if not os.path.exists(FEEDBACK_LOG_PATH):
        return {}
    try:
        with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Ошибка чтения feedback_log.json: {e}")
        return {}

def save_feedback_log(log_data):
    with open(FEEDBACK_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def can_send_feedback(user_id):
    log = load_feedback_log()
    if str(user_id) not in log:
        return True, None
    last_time = datetime.fromisoformat(log[str(user_id)])
    now = datetime.now()
    delta = now - last_time
    if delta > timedelta(hours=24):
        return True, None
    time_left = timedelta(hours=24) - delta
    return False, time_left

async def show_store_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    try:
        index = int(query.data.replace("store_", ""))
        region = context.user_data.get("region")
        city = context.user_data.get("city")

        if not region or not city:
            await query.edit_message_text("Ошибка: не выбран регион или город.")
            return

        store = stores_data[region][city][index]

        text = (
            f"🏬 <b>{store['name']}</b>\n"
            f"📍 <i>{store['address']}</i>\n"
            f"🕒 <pre>{store['hours']}</pre>"
        )

        keyboard = [
            [InlineKeyboardButton("🗺 Посмотреть на карте", url=store["map_url"])],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"city_{city}")]
        ]

        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await query.edit_message_text(f"Ошибка при открытии магазина: {e}")


async def review_regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    logger.info("▶️ review_regions вызван")
    query = update.callback_query
    await query.answer("Проверка возможности отправить отзыв...")

    user_id = update.effective_user.id
    allowed, time_left = can_send_feedback(user_id)

    if not allowed:
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes = remainder // 60
        msg = (f"⏳ Вы уже оставляли отзыв за последние 24 часа.\n"
               f"Следующий отзыв можно будет отправить через {time_left.days * 24 + hours} ч {minutes} мин.")

        keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="back_main")]]
        await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # если можно — продолжаем
    keyboard = [
        [InlineKeyboardButton(region, callback_data=f"review_region_{region}")]
        for region in stores_data.keys()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите область для отзыва:", reply_markup=reply_markup)

async def review_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    region = query.data.replace("review_region_", "")
    context.user_data['review_region'] = region

    keyboard = [
        [InlineKeyboardButton(city, callback_data=f"review_city_{city}")]
        for city in stores_data[region].keys()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='review')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Регион: {region}\nТеперь выберите город:", reply_markup=reply_markup)

async def review_shops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    city = query.data.replace("review_city_", "")
    region = context.user_data.get('review_region')
    context.user_data['review_city'] = city

    shops = stores_data[region][city]
    keyboard = [
        [InlineKeyboardButton(shop["name"], callback_data=f"review_shop_{index}")]
        for index, shop in enumerate(shops)
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"review_region_{region}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"{region} > {city}\nВыберите магазин:", reply_markup=reply_markup)

async def review_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    shop_index = int(query.data.replace("review_shop_", ""))
    region = context.user_data['review_region']
    city = context.user_data['review_city']
    shop = stores_data[region][city][shop_index]

    context.user_data['review_shop'] = shop
    context.user_data['review_shop_index'] = shop_index

    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="rating_1")],
        [InlineKeyboardButton("⭐⭐", callback_data="rating_2")],
        [InlineKeyboardButton("⭐⭐⭐", callback_data="rating_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_4")],
        [InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_5")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"review_city_{city}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Магазин: {shop['name']}\n\nОцените качество обслуживания:", reply_markup=reply_markup
    )
async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    rating = int(query.data.replace("rating_", ""))
    context.user_data['rating'] = rating

    keyboard = [
        [
            InlineKeyboardButton("🔙 Назад", callback_data=f"review_shop_{context.user_data['review_shop_index']}"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы поставили оценку: {'⭐' * rating}\n\nТеперь, пожалуйста, напишите отзыв только текстом в чат.",
        reply_markup=reply_markup
    )

    # Устанавливаем "ожидание текста" через conversation pattern
from telegram.ext import MessageHandler, filters

async def handle_review_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    if context.user_data.get("sent_review_prompt"):
        return  # Уже показывали — не дублируем

    user_message = update.message
    text = user_message.text

    if not text:
        return  # Если пришло не сообщение, а, например, стикер — игнорируем

    context.user_data['review_text'] = text
    context.user_data['sent_review_prompt'] = True  # Помечаем, что уже показали кнопки

    keyboard = [
        [InlineKeyboardButton("📩 Отправить отзыв", callback_data="send_review")],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_rating"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Спасибо! Всё готово для отправки отзыва.\nВы можете отправить его менеджеру 👇",
        reply_markup=reply_markup
    )


async def send_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    if not context.user_data.get('review_text'):
        await query.edit_message_text("Пожалуйста, напишите отзыв перед отправкой.")
        return

    user = update.effective_user
    region = context.user_data.get('review_region', '—')
    city = context.user_data.get('review_city', '—')
    shop = context.user_data.get('review_shop', {}).get('name', '—')
    rating = context.user_data.get('rating', '—')
    text = context.user_data.get('review_text', '—')
    photo = context.user_data.get('review_photo')

    review_message = (
        f"🛒 Отзыв от пользователя @{user.username or user.first_name}:\n"
        f"📍 {region} → {city} → {shop}\n"
        f"⭐ Оценка: {rating}\n"
        f"📝 Отзыв:\n{text}"
    )

    manager_chat_id = 568416622  # Можно заменить на ID, если будет

    # Отправка сообщения с фото или без
    if photo:
        await context.bot.send_photo(chat_id=manager_chat_id, photo=photo, caption=review_message)
    else:
        await context.bot.send_message(chat_id=manager_chat_id, text=review_message)

    # Ответ пользователю
    keyboard = [
        [InlineKeyboardButton("🏠 В главное меню", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("✅ Ваш отзыв отправлен менеджеру. Спасибо!", reply_markup=reply_markup)

    # Очистка user_data
    context.user_data.clear()
    # Логируем дату последнего отзыва
    feedback_log = load_feedback_log()
    feedback_log[str(user.id)] = datetime.now().isoformat()
    save_feedback_log(feedback_log)

async def submit_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    review_text = context.user_data.get('review_text', 'Без текста')
    username = update.effective_user.username or "Неизвестный пользователь"
    rating = context.user_data.get('rating', 'Не выбрана')
    shop = context.user_data.get('shop', 'Не выбран')

    message = (
        f"📩 Новый отзыв:\n"
        f"🏪 Магазин: {shop}\n"
        f"⭐ Оценка: {rating}\n"
        f"💬 Отзыв: {review_text}\n"
        f"👤 Пользователь: @{username}"
    )

    # Отправка менеджеру
    manager_id = '@nekuri_by_RB'  # можно заменить на ID, если известно
    await context.bot.send_message(chat_id=manager_id, text=message)

    await query.edit_message_text("✅ Отзыв отправлен менеджеру. Спасибо!")

async def show_socials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    text = (
        "📲 Мы в соцсетях:\n\n"
        "🔗 [Instagram](https://www.instagram.com/nekuri.by/)\n"
        "🔗 [Telegram канал](https://t.me/nekuri_by)\n"
        "🔗 [Telegram чат](https://t.me/nekuri_by_brest)\n"
        "🔗 [ВКонтакте](https://vk.com/nekuribrest)\n"
        "🔗 [TikTok](https://www.tiktok.com/@nekuri.by)"
    )

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    await query.answer()

    text = (
        "📞 Контактная информация:\n\n"
        "📱 *Горячая линия:* +375 (29) 225-13-34\n"
        "👤 *Менеджер:* [@nekuri_by_RB](https://t.me/nekuri_by_RB)\n"
        "🛒 *Интернет-магазин:* [nekuri.by](https://nekuri.by)\n"
        "📦 *Оптовый отдел:* [nekuri.by/OPT.html](https://nekuri.by/OPT.html)"
    )

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

# Заглушка для нажатий на кнопки
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    query = update.callback_query
    if not query:
        return
    data = query.data
    await query.answer()
    logger.info(f"Нажата кнопка: {data}")


    if data == 'addresses':
        await show_regions(update, context)
    elif data == "main_menu":
        await start(update, context)
    elif data == 'contacts':
        await show_contacts(update, context)
    elif data == 'socials':
        await show_socials(update, context)
    elif data == 'review':
        await review_regions(update, context)
    elif data.startswith('review_region_'):
        await review_cities(update, context)
    elif data.startswith('review_city_'):
        await review_shops(update, context)
    elif data.startswith('review_shop_'):
        await review_rating(update, context)
    elif data.startswith('rating_'):
        await handle_rating(update, context)
    elif data == 'send_review':
        await send_review(update, context)
    elif data == 'review_rating_back':
        await review_rating(update, context)
    elif data == 'back_main':
        await start(update, context)
    elif data.startswith('region_'):
        await show_cities(update, context)
    elif data.startswith('city_'):
        await show_stores(update, context)
    elif data.startswith("store_"):
        await show_store_info(update, context)
    else:
        await query.answer("В разработке 😉")


from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import difflib

async def public_city_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    text = update.message.text.strip().lower()
    all_cities = {
        city.lower(): (region, city)
        for region, cities in stores_data.items()
        for city in cities
    }
    closest = difflib.get_close_matches(text, all_cities.keys(), n=1, cutoff=0.6)

    if not closest:
        return

    matched_city = closest[0]
    region, city = all_cities[matched_city]
    city_hash = get_city_hash(city)  # Хешируем название города

    shops = stores_data[region][city]
    keyboard = [
        [InlineKeyboardButton(shop["name"], callback_data=f"public_store_{city_hash}_{i}")]
        for i, shop in enumerate(shops)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🏙 Магазины в {city}:", reply_markup=reply_markup)

async def public_store_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # Разбираем callback_data: public_store_<city_hash>_<shop_index>
        parts = query.data.split("_")
        if len(parts) != 4:  # Проверяем количество частей
            raise ValueError(f"Некорректный формат callback_data: {query.data}")

        city_hash = parts[2]  # Третья часть — хеш города
        shop_index = int(parts[3])  # Четвертая часть — индекс магазина

        # Находим город по хешу
        city = None
        region = None
        for reg, cities in stores_data.items():
            for city_name in cities:
                if get_city_hash(city_name) == city_hash:
                    city = city_name
                    region = reg
                    break
            if city:
                break

        if not city:
            await query.edit_message_text("Ошибка: город не найден.")
            return

        store = stores_data[region][city][shop_index]
        text = (
            f"🏬 <b>{store['name']}</b>\n"
            f"📍 <i>{store['address']}</i>\n"
            f"🕒 <pre>{store['hours']}</pre>"
        )
        keyboard = [
            [InlineKeyboardButton("🗺 Посмотреть на карте", url=store["map_url"])],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"public_back_{city_hash}")]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {str(e)}")
        logger.error(f"Ошибка в public_store_info: {e}, callback_data: {query.data}")


async def public_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # Разбираем callback_data: public_back_<city_hash>
        city_hash = query.data.replace("public_back_", "")

        # Находим город по хешу
        city = None
        region = None
        for reg, cities in stores_data.items():
            for city_name in cities:
                if get_city_hash(city_name) == city_hash:
                    city = city_name
                    region = reg
                    break
            if city:
                break

        if not city:
            await query.edit_message_text("Ошибка: город не найден.")
            return

        shops = stores_data[region][city]
        keyboard = [
            [InlineKeyboardButton(shop["name"], callback_data=f"public_store_{city_hash}_{i}")]
            for i, shop in enumerate(shops)
        ]
        await query.edit_message_text(
            f"🏙 Магазины в {city}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {str(e)}")
        logger.error(f"Ошибка в public_back: {e}, callback_data: {query.data}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(public_store_info, pattern=r"^public_store_"))
    app.add_handler(CallbackQueryHandler(public_back, pattern=r"^public_back_"))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_review_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.ChatType.PRIVATE, public_city_search))

    print("Бот запущен...")
    app.run_polling()





