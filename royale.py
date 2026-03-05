import logging
import random
import sqlite3
import asyncio
import json
import string
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ====================== КОНФИГУРАЦИЯ ======================
BOT_TOKEN = "8621386357:AAH9PFW3VJthdiVH596KtYtdVS4CL4aURIo"
ADMIN_IDS = [8480939483]  # ID админа

# Словари для хранения данных
games: Dict[int, Any] = {}
invites: Dict[str, int] = {}
# Словарь для отслеживания кто был шпионом в последних играх
spy_history: Dict[int, int] = defaultdict(int)

# ====================== ТЕМАТИКИ И ПЕРСОНАЖИ ======================
THEMES = {
    "clash": {
        "name": "🎮 Clash Royale",
        "emoji": "🎮",
        "characters": [
            "Рыцарь", "Варвары", "Арбалет", "Молния", "Ведьма", "Мега-Миньон", "Меганайт", "Принцесса",
            "Колдун", "Ледяной маг", "Электромаг", "Скелеты", "Банда гоблинов", "Графиня",
            "Хог райдер", "Гигант", "Пекка", "Дровосек", "Летучий дракон", "Мини-пекка", "Бревно",
            "Лучники", "Гоблины-копейщики", "Бомбер", "Бочка с варваром", "Огненный дух", "Феникс",
            "Монах", "Золотой рыцарь", "Скелеты-драконы", "Электро-дракон", "Землетрясение", "Ярость",
            "Зеркало", "Клон", "Пушка", "Инферно", "Ледяной дух", "Электро дух", "Огненный Шар",
            "Король скелетов", "Тёмный принц", "Принц", "Ледяной голем", "Голем", "Гигантский скелет",
            "Кладбище", "Заряд", "Снежок", "Торнадо", "Варварская бочка", "Гоблинская бочка",
            "Скелет-бомбер", "Страж", "Королевский призрак", "Бандит", "Охотник", "Рыбак",
            "Валкирия", "Мушкетёрша", "Королевский гигант(с пушкой)", "Элитные варвары", "Королевские рекруты"
        ]
    },
    "brawl": {
        "name": "⭐ Brawl Stars",
        "emoji": "⭐",
        "characters": [
            "Шелли", "Кольт", "Булл", "Динамайк", "Нита", "Эль Примо", "Брок", "Бо", "Пайпер",
            "Барли", "Тара", "Пэм", "Фрэнк", "Дэррил", "Спайк", "Леон", "Сэнди", "Ворон", "Гейл",
            "Биби", "Эдгар", "Макс", "Джесси", "Рико", "Карл", "Роза", "Джин", "Вольт",
            "Лу", "Мортис", "Мэнди", "Честер", "Чарли", "Спайк", "Хэнк", "Мейси", "Грей",
            "Генерал Гавс", "Базз", "Бонни", "Мэг", "Фэнг", "Грифф", "Френк", "Спраут", "Корделиус"
        ]
    },
    "memes": {
        "name": "😂 приколы мемы",
        "emoji": "😂",
        "characters": [
            "Гигачад", "Сигма", "Сигма бой", "данил калбасенка", "Амогус", "helio137", "NPC", "Skibidi Toilet",
            "Мистер Бист", "Илон Маск", "Криштиану Роналду", "Лионель Месси", "Неймар", "Дуэйн Джонсон",
            "Ева Эльфи", "Дженни Китти", "Диана Райдер", "Дрейк", "зубареф",
            "Сталин", "Кот Батон", "Ждун",
            "Стинт", "Гитлер", "Тоха 2Х2",  "Троллфейс",
            "Пепе", "Краш", "Свити Фокс", "Я чо упоротый", "Бибизяна"
        ]
    },
    "heroes": {
        "name": "🦸 Супергерои",
        "emoji": "🦸",
        "characters": [
            "Человек-паук", "Бэтмен", "Супермен", "Железный человек", "Халк", "Тор", "Капитан Америка",
            "Дэдпул", "Локи", "Танос", "Доктор Стрэндж", "Чёрная вдова", "Росомаха", "Харли Квинн",
            "Веном", "Человек-муравей", "Стражи Галактики", "Аквамен", "Флеш", "Джокер", "Робин",
            "Зелёный фонарь", "Чудо-женщина", 
            "Призрачный гонщик",
            "Циклоп", "Росомаха",  "Капитан Марвел", "Чёрная пантера"
        ]
    },
    "cartoons": {
        "name": "🍔 Мультфильмы",
        "emoji": "🍔",
        "characters": [
            "Шрек", "Губка Боб", "Патрик", "Скуби-Ду", "Гомер Симпсон", "Барт Симпсон",
            "Микки Маус", "Винни Пух", "Пятачок", "Нуф-Нуф", "Ниф-Ниф", "Наф-Наф",
            "Маша", "Медведь", "Лунтик", "Фиксики", "Нолик", "Симка", "Шиммер", "Шайн",
            "Крош", "Ёжик", "Нюша", "Бараш", "Лосяш", "Кар-Карыч", "Копатыч", "Пин",
            "Бен 10", "Гуфи", "Дональд Дак", "Дейзи Дак", "Чип", "Дейл", "Гайка", "Рокфор",
            "Вжик", "Том", "Джерри", "Багз Банни", "Даффи Дак", "Порки Пиг", "Элмер Фадд"
        ]
    },
    "random": {
        "name": "🎲 Всё вместе",
        "emoji": "🎲",
        "characters": []  # Будет заполняться из всех тем
    }
}

# Заполняем random тему всеми персонажами
all_characters = []
for theme_key, theme_data in THEMES.items():
    if theme_key != "random":
        all_characters.extend(theme_data["characters"])
THEMES["random"]["characters"] = all_characters

# Премиум-функции
PREMIUM_FEATURES = {
    "first_letter": {
        "name": "🔤 Первая буква",
        "description": "Узнать первую букву загаданного персонажа",
        "price": 20,
        "emoji": "🔤",
        "usage_limit": 3,
        "command": "/first_letter"
    },
    "last_letter": {
        "name": "🔚 Последняя буква",
        "description": "Узнать последнюю букву загаданного персонажа",
        "price": 20,
        "emoji": "🔚",
        "usage_limit": 3,
        "command": "/last_letter"
    },
    "always_spy": {
        "name": "🕵️ Всегда шпион",
        "description": "Гарантированно стать шпионом (3 игры)",
        "price": 30,
        "emoji": "🕵️",
        "usage_limit": 3,
        "command": None
    },
    "never_spy": {
        "name": "👥 Никогда не шпион",
        "description": "Гарантированно быть мирным (3 игры)",
        "price": 30,
        "emoji": "👥",
        "usage_limit": 3,
        "command": None
    }
}

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ====================== БАЗА ДАННЫХ ======================
def init_db():
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if c.fetchone():
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        if 'stars_spent' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN stars_spent INTEGER DEFAULT 0")
    else:
        c.execute('''CREATE TABLE users
                     (id INTEGER PRIMARY KEY,
                      username TEXT,
                      first_name TEXT,
                      premium TEXT DEFAULT '{}',
                      total_games INTEGER DEFAULT 0,
                      total_wins INTEGER DEFAULT 0,
                      stars_spent INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS purchases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  feature TEXT,
                  amount INTEGER,
                  stars INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def get_user(user_id: int) -> Optional[Tuple]:
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id: int, username: str, first_name: str):
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, first_name) VALUES (?, ?, ?)",
              (user_id, username, first_name))
    conn.commit()
    conn.close()

def get_premium(user_id: int) -> Dict:
    user = get_user(user_id)
    if user and user[3]:
        return json.loads(user[3])
    return {}

def update_premium(user_id: int, premium_dict: Dict):
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET premium=? WHERE id=?", (json.dumps(premium_dict), user_id))
    conn.commit()
    conn.close()

def add_purchase(user_id: int, feature: str, amount: int, stars: int):
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("INSERT INTO purchases (user_id, feature, amount, stars) VALUES (?, ?, ?, ?)",
              (user_id, feature, amount, stars))
    c.execute("UPDATE users SET stars_spent = stars_spent + ? WHERE id=?", (stars, user_id))
    conn.commit()
    conn.close()

def increment_user_stats(user_id: int, game_won: bool = False):
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET total_games = total_games + 1 WHERE id=?", (user_id,))
    if game_won:
        c.execute("UPDATE users SET total_wins = total_wins + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def add_premium_to_user(user_id: int, feature: str, amount: int):
    premium = get_premium(user_id)
    if feature not in premium:
        premium[feature] = 0
    premium[feature] += amount
    update_premium(user_id, premium)

def get_all_users() -> List[Tuple]:
    """Получить всех пользователей из БД"""
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, total_games, stars_spent, created_at FROM users ORDER BY id")
    users = c.fetchall()
    conn.close()
    return users

# ====================== КЛАСС ИГРЫ ======================
class SpyGame:
    def __init__(self, chat_id: int, total_players: int, creator_id: int, theme: str = "random"):
        self.chat_id = chat_id
        self.total_players = total_players
        self.creator_id = creator_id
        self.theme = theme
        self.players = []
        self.spy_index = None
        self.character = None
        self.invite_code = self.generate_invite_code()
        self.started = False
        self.used_features = {}
        self.created_at = datetime.now()
        self.lobby_message_id = None

    def generate_invite_code(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def add_player(self, user_id: int, user_name: str) -> bool:
        for p in self.players:
            if p['id'] == user_id:
                return False
        self.players.append({'id': user_id, 'name': user_name})
        return True

    def get_player_name(self, user_id: int) -> Optional[str]:
        for p in self.players:
            if p['id'] == user_id:
                return p['name']
        return None

    def assign_roles(self):
        """Назначает роли с учётом премиум-функций и истории шпионов"""
        global spy_history
        
        # Выбираем случайного персонажа из выбранной темы
        theme_characters = THEMES[self.theme]["characters"]
        self.character = random.choice(theme_characters)
        
        n = len(self.players)
        
        # Определяем кандидатов в шпионы с учётом премиум-функций
        spy_candidates = []
        peaceful_candidates = []
        
        for i, p in enumerate(self.players):
            uid = p['id']
            prem = get_premium(uid)
            always = prem.get('always_spy', 0)
            never = prem.get('never_spy', 0)
            
            if always > 0:
                spy_candidates.append(i)
            elif never > 0:
                peaceful_candidates.append(i)
        
        # Если есть кандидаты с always_spy, выбираем из них
        if spy_candidates:
            # Но уменьшаем вероятность для тех, кто недавно был шпионом
            weighted_candidates = []
            for idx in spy_candidates:
                uid = self.players[idx]['id']
                weight = max(1, 5 - spy_history.get(uid, 0))  # Чем чаще был шпионом, тем меньше вес
                weighted_candidates.extend([idx] * weight)
            
            self.spy_index = random.choice(weighted_candidates)
            uid = self.players[self.spy_index]['id']
            
            # Уменьшаем счётчик always_spy
            prem = get_premium(uid)
            prem['always_spy'] -= 1
            if prem['always_spy'] <= 0:
                del prem['always_spy']
            update_premium(uid, prem)
            
            # Увеличиваем счётчик шпиона
            spy_history[uid] += 1
            
        else:
            # Ищем кандидатов среди обычных игроков
            possible_indices = [i for i in range(n) if i not in peaceful_candidates]
            
            if not possible_indices:
                possible_indices = list(range(n))
            
            # Весовая вероятность: чем реже был шпионом, тем выше шанс
            weighted_possible = []
            for idx in possible_indices:
                uid = self.players[idx]['id']
                weight = max(1, 5 - spy_history.get(uid, 0))
                weighted_possible.extend([idx] * weight)
            
            self.spy_index = random.choice(weighted_possible)
            uid = self.players[self.spy_index]['id']
            
            # Увеличиваем счётчик шпиона
            spy_history[uid] += 1
        
        # Обрабатываем never_spy для остальных
        for i, p in enumerate(self.players):
            if i != self.spy_index:
                uid = p['id']
                prem = get_premium(uid)
                if 'never_spy' in prem:
                    prem['never_spy'] -= 1
                    if prem['never_spy'] <= 0:
                        del prem['never_spy']
                    update_premium(uid, prem)

# ====================== СОСТОЯНИЯ ======================
class GameStates(StatesGroup):
    waiting_for_players_count = State()
    waiting_for_theme = State()
    admin_mailing_text = State()
    admin_add_user = State()
    admin_add_feature = State()
    admin_add_amount = State()

# ====================== КЛАВИАТУРЫ ======================
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 СОЗДАТЬ ИГРУ", callback_data="create_game")
    builder.button(text="⭐ ПРЕМИУМ", callback_data="premium_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_back_keyboard(callback_data: str = "back_to_main"):
    builder = InlineKeyboardBuilder()
    builder.button(text="◀ НАЗАД", callback_data=callback_data)
    return builder.as_markup()

def get_theme_keyboard():
    builder = InlineKeyboardBuilder()
    for theme_key, theme_data in THEMES.items():
        builder.button(
            text=f"{theme_data['emoji']} {theme_data['name']}",
            callback_data=f"theme_{theme_key}"
        )
    builder.button(text="◀ НАЗАД", callback_data="back_to_main")
    builder.adjust(2)
    return builder.as_markup()

def get_premium_keyboard(user_premium: Dict):
    builder = InlineKeyboardBuilder()
    for key, feature in PREMIUM_FEATURES.items():
        if key not in user_premium or user_premium[key] <= 0:
            builder.button(text=f"{feature['emoji']} {feature['name']} - {feature['price']} ⭐", callback_data=f"buy_{key}")
        else:
            builder.button(text=f"{feature['emoji']} {feature['name']} ✅ {user_premium[key]}", callback_data="already_bought")
    builder.button(text="◀ НАЗАД", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def get_game_keyboard(game_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ПРИСОЕДИНИТЬСЯ", callback_data=f"game_join_{game_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 РАССЫЛКА", callback_data="admin_mailing")
    builder.button(text="➕ ВЫДАТЬ ПРЕМИУМ", callback_data="admin_add_premium")
    builder.button(text="📊 СТАТИСТИКА", callback_data="admin_stats")
    builder.button(text="◀ НАЗАД", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

# ====================== ОБРАБОТЧИКИ КОМАНД ======================
@dp.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    args = command.args
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name)

    if args and args in invites:
        game_id = invites[args]
        if game_id in games:
            game = games[game_id]
            
            if game.started:
                await message.answer("❌ Игра уже началась!")
                return
            if len(game.players) >= game.total_players:
                await message.answer("❌ Игра уже заполнена!")
                return
            
            if game.add_player(message.from_user.id, message.from_user.full_name):
                await message.answer(f"✅ Вы присоединились к игре! ({len(game.players)}/{game.total_players})")
                await update_game_lobby(game)
                if len(game.players) == game.total_players:
                    await start_game(game)
                return
            else:
                await message.answer("❌ Вы уже в игре!")
                return
        else:
            await message.answer("❌ Игра не найдена")
            return

    welcome_text = (
        "🔍 Добро пожаловать в игру «Кто шпион: Всё в одном»!\n\n"
        "🎮 Для компании друзей\n"
        "Теперь с разными тематиками:\n"
        "• Clash Royale\n"
        "• Brawl Stars\n"
        "• Мемы\n"
        "• Супергерои\n"
        "• Мультфильмы\n"
        "• Аниме\n"
        "• Видеоигры\n\n"
        "📌 Как играть:\n"
        "1. Создайте игру\n"
        "2. Пригласите друзей по ссылке\n"
        "3. Все видят общее лобби\n"
        "4. Получите роли и обсуждайте\n\n"
        "👇 Выберите действие:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await message.answer(
        "👨‍💼 **Админ-панель**\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

@dp.message(Command("create"))
async def cmd_create(message: Message, state: FSMContext):
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name)
    await message.answer(
        "🔢 Сколько игроков?\n\nВведите число от 3 до 10:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(GameStates.waiting_for_players_count)

@dp.message(GameStates.waiting_for_players_count)
async def process_players_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 3 or count > 10:
            await message.answer("❌ Число должно быть от 3 до 10. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return

    await state.update_data(players_count=count)
    
    # Предлагаем выбрать тематику
    await message.answer(
        "🎭 **Выберите тематику игры:**",
        reply_markup=get_theme_keyboard()
    )
    await state.set_state(GameStates.waiting_for_theme)

@dp.callback_query(F.data.startswith("theme_"))
async def process_theme(callback: CallbackQuery, state: FSMContext):
    theme = callback.data.replace("theme_", "")
    
    if theme not in THEMES:
        await callback.answer("❌ Тема не найдена", show_alert=True)
        return
    
    data = await state.get_data()
    count = data.get('players_count')
    
    if not count:
        await callback.answer("❌ Ошибка создания игры", show_alert=True)
        await state.clear()
        return
    
    chat_id = callback.message.chat.id
    game = SpyGame(chat_id, count, callback.from_user.id, theme)
    game.add_player(callback.from_user.id, callback.from_user.full_name)
    games[chat_id] = game
    invites[game.invite_code] = chat_id

    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start={game.invite_code}"

    theme_name = THEMES[theme]["name"]
    theme_emoji = THEMES[theme]["emoji"]
    
    lobby_text = (
        f"🎮 **ЛОББИ ИГРЫ**\n\n"
        f"{theme_emoji} **Тема:** {theme_name}\n"
        f"👤 **Создатель:** {callback.from_user.full_name}\n"
        f"👥 **Игроков:** 1/{count}\n\n"
        f"📨 **Ссылка для друзей:**\n{link}\n\n"
        f"🔑 **Код:** {game.invite_code}\n\n"
        f"ℹ️ Отправьте ссылку друзьям, они увидят это же лобби"
    )
    
    msg = await callback.message.edit_text(lobby_text, reply_markup=get_game_keyboard(chat_id))
    game.lobby_message_id = msg.message_id
    await state.clear()
    await callback.answer()

async def update_game_lobby(game: SpyGame):
    if not game.lobby_message_id:
        return
    
    players_list = "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(game.players)])
    theme_name = THEMES[game.theme]["name"]
    theme_emoji = THEMES[game.theme]["emoji"]
    
    lobby_text = (
        f"🎮 **ЛОББИ ИГРЫ**\n\n"
        f"{theme_emoji} **Тема:** {theme_name}\n"
        f"👤 **Создатель:** {game.players[0]['name']}\n"
        f"👥 **Участники:**\n{players_list}\n"
        f"📊 **Осталось мест:** {game.total_players - len(game.players)}/{game.total_players}\n\n"
        f"🔑 **Код:** {game.invite_code}"
    )
    
    try:
        await bot.edit_message_text(
            lobby_text,
            chat_id=game.chat_id,
            message_id=game.lobby_message_id,
            reply_markup=get_game_keyboard(game.chat_id)
        )
    except Exception as e:
        logger.error(f"Ошибка обновления лобби: {e}")

@dp.message(Command("first_letter"))
async def cmd_first_letter(message: Message):
    user_id = message.from_user.id
    prem = get_premium(user_id)
    
    if 'first_letter' not in prem or prem['first_letter'] <= 0:
        await message.answer("❌ У вас нет активных использований «Первой буквы». Купите в ⭐ Премиум!")
        return
    
    for game_id, game in games.items():
        if game.started and any(p['id'] == user_id for p in game.players):
            if user_id in game.used_features and game.used_features[user_id].get('first_letter', 0) >= 1:
                await message.answer("❌ Вы уже использовали эту функцию в текущей игре.")
                return
            
            first_letter = game.character[0] if game.character else "?"
            await message.answer(f"🔤 Первая буква: {first_letter}")
            
            if user_id not in game.used_features:
                game.used_features[user_id] = {}
            game.used_features[user_id]['first_letter'] = game.used_features[user_id].get('first_letter', 0) + 1
            
            prem['first_letter'] -= 1
            if prem['first_letter'] <= 0:
                del prem['first_letter']
            update_premium(user_id, prem)
            return
    
    await message.answer("❌ Вы не в игре или игра не началась.")

@dp.message(Command("last_letter"))
async def cmd_last_letter(message: Message):
    user_id = message.from_user.id
    prem = get_premium(user_id)
    
    if 'last_letter' not in prem or prem['last_letter'] <= 0:
        await message.answer("❌ У вас нет активных использований «Последней буквы». Купите в ⭐ Премиум!")
        return
    
    for game_id, game in games.items():
        if game.started and any(p['id'] == user_id for p in game.players):
            if user_id in game.used_features and game.used_features[user_id].get('last_letter', 0) >= 1:
                await message.answer("❌ Вы уже использовали эту функцию в текущей игре.")
                return
            
            last_letter = game.character[-1] if game.character else "?"
            await message.answer(f"🔚 Последняя буква: {last_letter}")
            
            if user_id not in game.used_features:
                game.used_features[user_id] = {}
            game.used_features[user_id]['last_letter'] = game.used_features[user_id].get('last_letter', 0) + 1
            
            prem['last_letter'] -= 1
            if prem['last_letter'] <= 0:
                del prem['last_letter']
            update_premium(user_id, prem)
            return
    
    await message.answer("❌ Вы не в игре или игра не началась.")

# ====================== ОБРАБОТЧИКИ КОЛБЭКОВ ======================
@dp.callback_query(F.data == "create_game")
async def callback_create_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_create(callback.message, state)

@dp.callback_query(F.data == "premium_menu")
async def callback_premium_menu(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    prem = get_premium(user_id)
    text = "⭐ **Премиум магазин**\n\nВыберите функцию для покупки (цены в Telegram Stars):"
    await callback.message.edit_text(text, reply_markup=get_premium_keyboard(prem))

@dp.callback_query(F.data == "already_bought")
async def callback_already_bought(callback: CallbackQuery):
    await callback.answer("✅ У вас уже есть эта функция!", show_alert=True)

@dp.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: CallbackQuery, state: FSMContext):
    feature_key = callback.data[4:]
    
    logger.info(f"Покупка функции: {feature_key}")
    logger.info(f"Доступные функции: {list(PREMIUM_FEATURES.keys())}")
    
    if feature_key not in PREMIUM_FEATURES:
        await callback.answer(f"Ошибка: функция '{feature_key}' не найдена", show_alert=True)
        return
    
    feature = PREMIUM_FEATURES[feature_key]
    await state.update_data(selected_feature=feature_key)
    
    prices = [types.LabeledPrice(label=feature['name'], amount=feature['price'])]
    
    try:
        await callback.message.answer_invoice(
            title=f"Покупка: {feature['name']}",
            description=f"{feature['description']}\nКоличество: {feature['usage_limit']} шт.",
            provider_token="",
            currency="XTR",
            prices=prices,
            payload=feature_key
        )
        await callback.answer("✅ Счёт создан! Проверьте новые сообщения.")
    except Exception as e:
        logger.error(f"Ошибка при создании инвойса: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже.",
            reply_markup=get_back_keyboard("premium_menu")
        )

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    stars = message.successful_payment.total_amount
    
    if payload in PREMIUM_FEATURES:
        feature = PREMIUM_FEATURES[payload]
        
        premium = get_premium(user_id)
        if payload not in premium:
            premium[payload] = 0
        premium[payload] += feature['usage_limit']
        update_premium(user_id, premium)
        
        add_purchase(user_id, payload, feature['usage_limit'], stars)
        
        await message.answer(
            f"✅ **Оплата прошла успешно!**\n\n"
            f"Функция {feature['name']} активирована.\n"
            f"Количество: {feature['usage_limit']} шт.\n\n"
            f"Спасибо за покупку! 🎉"
        )

@dp.callback_query(F.data.startswith("game_join_"))
async def callback_game_join(callback: CallbackQuery):
    game_id = int(callback.data.split("_")[2])
    
    if game_id not in games:
        await callback.answer("Игра не найдена", show_alert=True)
        return
    
    game = games[game_id]
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    create_user(user_id, callback.from_user.username or "", user_name)
    
    if game.started:
        await callback.answer("Игра уже началась!", show_alert=True)
        return
    if len(game.players) >= game.total_players:
        await callback.answer("Игра уже заполнена!", show_alert=True)
        return
    
    if game.add_player(user_id, user_name):
        await callback.answer("✅ Вы присоединились!")
        await update_game_lobby(game)
        if len(game.players) == game.total_players:
            await start_game(game)
    else:
        await callback.answer("Вы уже в игре!", show_alert=True)

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    await callback.answer()
    class MockCommand:
        def __init__(self):
            self.args = None
    await cmd_start(callback.message, MockCommand())

@dp.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👨‍💼 **Админ-панель**\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

# ====================== АДМИН-ПАНЕЛЬ (ОСТАВИЛ ТОЛЬКО НУЖНОЕ) ======================
@dp.callback_query(F.data == "admin_mailing")
async def callback_admin_mailing(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 **Рассылка**\n\n"
        "Введите текст для рассылки всем пользователям:",
        reply_markup=get_back_keyboard("admin")
    )
    await state.set_state(GameStates.admin_mailing_text)
    await callback.answer()

@dp.message(GameStates.admin_mailing_text)
async def process_admin_mailing(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    text = message.text
    
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = c.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    await message.answer(f"📢 Начинаю рассылку {len(users)} пользователям...")
    
    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(
                user_id,
                f"📢 **Рассылка от администратора**\n\n{text}"
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await message.answer(
        f"✅ **Рассылка завершена**\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )
    await state.clear()

@dp.callback_query(F.data == "admin_add_premium")
async def callback_admin_add_premium(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ **Выдача премиума**\n\n"
        "Введите ID пользователя:",
        reply_markup=get_back_keyboard("admin")
    )
    await state.set_state(GameStates.admin_add_user)
    await callback.answer()

@dp.message(GameStates.admin_add_user)
async def process_admin_add_user(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите число:")
        return
    
    await state.update_data(target_user_id=user_id)
    
    features_text = "Выберите функцию:\n\n"
    for key, feature in PREMIUM_FEATURES.items():
        features_text += f"{key} - {feature['name']}\n"
    
    await message.answer(
        f"➕ **Выдача премиума пользователю {user_id}**\n\n"
        f"{features_text}\n"
        f"Введите ключ функции (first_letter, last_letter, always_spy, never_spy):",
        reply_markup=get_back_keyboard("admin")
    )
    await state.set_state(GameStates.admin_add_feature)

@dp.message(GameStates.admin_add_feature)
async def process_admin_add_feature(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    feature_key = message.text.strip().lower()
    if feature_key not in PREMIUM_FEATURES:
        await message.answer("❌ Неверный ключ функции. Попробуйте снова:")
        return
    
    await state.update_data(feature_key=feature_key)
    
    await message.answer(
        f"➕ Введите количество использований:",
        reply_markup=get_back_keyboard("admin")
    )
    await state.set_state(GameStates.admin_add_amount)

@dp.message(GameStates.admin_add_amount)
async def process_admin_add_amount(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число:")
        return
    
    data = await state.get_data()
    user_id = data['target_user_id']
    feature_key = data['feature_key']
    
    add_premium_to_user(user_id, feature_key, amount)
    
    feature_name = PREMIUM_FEATURES[feature_key]['name']
    
    await message.answer(
        f"✅ **Премиум выдан!**\n\n"
        f"👤 Пользователь: {user_id}\n"
        f"📦 Функция: {feature_name}\n"
        f"🔢 Количество: {amount} шт.\n\n"
        f"Пользователь получит функцию при следующем входе в игру."
    )
    
    try:
        await bot.send_message(
            user_id,
            f"🎁 **Вам выдан премиум!**\n\n"
            f"Функция: {feature_name}\n"
            f"Количество: {amount} шт.\n\n"
            f"Используйте в игре!"
        )
    except:
        pass
    
    await state.clear()

@dp.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    conn = sqlite3.connect('spy_game.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT SUM(stars_spent) FROM users")
    total_stars = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM purchases")
    total_purchases = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE total_games > 0")
    active_users = c.fetchone()[0]
    conn.close()
    
    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🎮 Игравших: {active_users}\n"
        f"💰 Всего потрачено Stars: {total_stars} ⭐\n"
        f"📦 Всего покупок: {total_purchases}\n"
        f"🎮 Активных игр: {len(games)}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard("admin"))

# ====================== ЗАПУСК ИГРЫ (БЕЗ СООБЩЕНИЯ О ЗАВЕРШЕНИИ) ======================
async def start_game(game: SpyGame):
    game.assign_roles()
    game.started = True
    
    theme_name = THEMES[game.theme]["name"]
    theme_emoji = THEMES[game.theme]["emoji"]
    
    if game.lobby_message_id:
        try:
            await bot.edit_message_text(
                f"🎮 **ИГРА НАЧАЛАСЬ!**\n\n{theme_emoji} Тема: {theme_name}\n\n✅ Все игроки получили роли в личные сообщения.\n🔍 Обсуждайте и вычисляйте шпиона!",
                game.chat_id,
                game.lobby_message_id
            )
        except Exception as e:
            logger.error(f"Ошибка обновления лобби при старте: {e}")
    
    for i, p in enumerate(game.players):
        uid = p['id']
        if i == game.spy_index:
            role_text = (
                f"🕵️ **ВЫ ШПИОН!**\n\n"
                f"📌 Тема: {theme_name} {theme_emoji}\n"
                f"Ваша задача:\n"
                f"• Вычислить карту мирных\n"
                f"• Остаться незамеченным\n\n"
                f"🎴 Карта мирных: ???"
            )
        else:
            role_text = (
                f"🎴 **ВАША КАРТА:** {game.character}\n\n"
                f"📌 Тема: {theme_name} {theme_emoji}\n"
                f"Вы мирный житель.\n"
                f"Найдите шпиона в компании!"
            )
        
        prem = get_premium(uid)
        premium_text = ""
        if 'first_letter' in prem and prem['first_letter'] > 0:
            premium_text += "\n🔤 /first_letter - узнать первую букву"
        if 'last_letter' in prem and prem['last_letter'] > 0:
            premium_text += "\n🔚 /last_letter - узнать последнюю букву"
        
        if premium_text:
            role_text += f"\n\n✨ **Ваши премиум функции:**{premium_text}"
        
        try:
            await bot.send_message(uid, f"🎮 **ИГРА НАЧАЛАСЬ!**\n\n{role_text}")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение игроку {uid}: {e}")

# ====================== ЗАПУСК БОТА ======================
async def main():
    init_db()
    logger.info("Бот запущен")
    print("="*50)
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
    print("="*50)
    bot_info = await bot.get_me()
    print(f"👤 Админ: {ADMIN_IDS}")
    print(f"🤖 Бот: @{bot_info.username}")
    print(f"💰 Оплата: Telegram Stars")
    print(f"🎭 Тем: {len(THEMES)}")
    print("✅ Доступные премиум функции:", list(PREMIUM_FEATURES.keys()))
    print("="*50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())