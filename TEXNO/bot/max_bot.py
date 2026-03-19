import asyncio
import logging
import os
from dotenv import load_dotenv
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, CallbackQuery
from maxapi.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import Database

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('MAX_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Не найден MAX_BOT_TOKEN в .env файле")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

def make_keyboard(buttons_data):
    inline_keyboard = []
    for row in buttons_data:
        keyboard_row = []
        for text, callback in row:
            keyboard_row.append(InlineKeyboardButton(text=text, callback_data=callback))
        inline_keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

async def get_user_from_event(event):
    user_id = str(event.sender.id) if hasattr(event, 'sender') else str(event.user_id)
    username = getattr(event.sender, 'username', None) if hasattr(event, 'sender') else None
    first_name = getattr(event.sender, 'first_name', None) if hasattr(event, 'sender') else None
    last_name = getattr(event.sender, 'last_name', None) if hasattr(event, 'sender') else None
    return db.get_or_create_user(user_id, username, first_name, last_name)

@dp.bot_started()
async def on_bot_started(event: BotStarted):
    user = await get_user_from_event(event)
    db.log_action(user['user_id'], 'bot_start', '/start')
    
    keyboard = make_keyboard([
        [("📋 Меры поддержки и технологические услуги", "main_menu")]
    ])
    
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="Добро пожаловать! Выберите раздел:",
        reply_markup=keyboard
    )

@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    user = await get_user_from_event(event)
    db.log_action(user['user_id'], 'command_start', '/start')
    
    keyboard = make_keyboard([
        [("📋 Меры поддержки и технологические услуги", "main_menu")]
    ])
    
    await event.message.answer(
        text="Добро пожаловать! Выберите раздел:",
        reply_markup=keyboard
    )

@dp.message_created(Command('help'))
async def help_command(event: MessageCreated):
    await event.message.answer(
        text="Команды:\n/start - Начать работу\n/help - Помощь"
    )

@dp.callback_query()
async def handle_callback(event: CallbackQuery):
    data = event.data
    user = await get_user_from_event(event)
    db.log_action(user['user_id'], 'button_press', data)
    
    if data == "main_menu":
        keyboard = make_keyboard([
            [("1. Финансовые услуги", "cat_finance")],
            [("2. Программы развития", "cat_development")],
            [("3. Доступ к инфраструктуре", "cat_infrastructure")]
        ])
        await event.message.edit_text(
            text="Что вы хотите получить?",
            reply_markup=keyboard
        )
        await event.answer()
    
    elif data == "cat_finance":
        keyboard = make_keyboard([
            [("1.1 Запуск бизнеса", "sub_startup")],
            [("1.2 Программы финансирования", "sub_funding")],
            [("1.3 Частные инвестиции", "sub_investments")],
            [("◀️ Назад", "main_menu")]
        ])
        await event.message.edit_text(
            text="Финансовые услуги:",
            reply_markup=keyboard
        )
        await event.answer()
    
    elif data == "cat_development":
        keyboard = make_keyboard([
            [("2.1 Резидентура в технопарк СПб", "sub_residence")],
            [("2.2 Гос программы", "sub_gov")],
            [("2.3 Протестировать программы и выйти на рынок", "sub_market")],
            [("◀️ Назад", "main_menu")]
        ])
        await event.message.edit_text(
            text="Программы развития:",
            reply_markup=keyboard
        )
        await event.answer()
    
    elif data == "cat_infrastructure":
        keyboard = make_keyboard([
            [("3.1 Технопарк СПб", "sub_technopark")],
            [("3.2 Объекты инновационно технологической инфраструктуры", "sub_innovation")],
            [("3.3 Технологические компании", "sub_tech_companies")],
            [("3.4 Технологические услуги", "sub_tech_services")],
            [("◀️ Назад", "main_menu")]
        ])
        await event.message.edit_text(
            text="Доступ к инфраструктуре:",
            reply_markup=keyboard
        )
        await event.answer()
    
    elif data in ["sub_startup", "sub_funding", "sub_investments", 
                  "sub_residence", "sub_gov", "sub_market",
                  "sub_technopark", "sub_innovation", "sub_tech_companies", "sub_tech_services"]:
        
        link_data = db.get_link_by_menu_code(data)
        
        if link_data:
            db.log_action(user['user_id'], 'view_link', data, {'link_code': link_data['code']})
            
            keyboard = make_keyboard([
                [("🔗 Перейти по ссылке", f"link_{link_data['code']}")],
                [("◀️ Назад", f"cat_{link_data['parent_category']}")],
                [("🏠 Главное меню", "main_menu")]
            ])
            
            await event.message.edit_text(
                text=f"{link_data['name']}\n\n{link_data['url']}",
                reply_markup=keyboard
            )
        else:
            await event.message.edit_text(
                text="❌ Информация временно недоступна",
                reply_markup=make_keyboard([[("◀️ Назад", "main_menu")]])
            )
        await event.answer()
    
    elif data.startswith("link_"):
        link_code = data.replace("link_", "")
        link_data = db.get_link_by_code(link_code)
        
        if link_data:
            db.log_link_click(link_code, user['user_id'])
            await event.answer(f"🔗 Открываю {link_data['name']}...")
        else:
            await event.answer("❌ Ссылка не найдена")

async def main():
    logger.info("Запуск MAX бота...")
    links_count = len(db.get_all_links())
    logger.info(f"Загружено {links_count} ссылок")
    
    try:
        await bot.delete_webhook()
    except:
        pass
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")