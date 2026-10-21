import asyncio, random, logging, json, os, time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = ""
bot = Bot(token=TOKEN)
dp = Dispatcher()
GAME_FILE = "game_data.json"

def load_data(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: return {}
    return {}
def save_data(f, d):
    try:
        with open(f, "w", encoding="utf-8") as file: json.dump(d, file, ensure_ascii=False, indent=4)
    except Exception as e: logging.error(f"Ошибка: {e}")

game_data = load_data(GAME_FILE)

main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🎮 Майнинг-Ферма")]], resize_keyboard=True)

game_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⛏ Майнить", callback_data="mine_click")],
    [InlineKeyboardButton(text="🌱 Трава", callback_data="grass_menu"), InlineKeyboardButton(text="💼 Бизнес и Дома", callback_data="prop_menu")],
    [InlineKeyboardButton(text="💱 Банк", callback_data="bank_menu"), InlineKeyboardButton(text="🎰 Казино", callback_data="casino_menu")],
    [InlineKeyboardButton(text="👷 Работа", callback_data="work_job"), InlineKeyboardButton(text="🛠 Улучшения", callback_data="mine_upgrades")],
    [InlineKeyboardButton(text="🏆 Топ-10", callback_data="mine_top"), InlineKeyboardButton(text="🎁 Бонус", callback_data="mine_bonus")],
])

prop_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏘 Дома", callback_data="house_menu")],
    [InlineKeyboardButton(text="💼 Бизнесы", callback_data="business_menu")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")]
])

bank_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💵 Купить USD", callback_data="bank_buy_usd"), InlineKeyboardButton(text="💴 Купить CNY", callback_data="bank_buy_cny")],
    [InlineKeyboardButton(text="🪙 Купить BTC", callback_data="bank_buy_btc")],
    [InlineKeyboardButton(text="💸 Продать всё", callback_data="bank_sell_all")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")]
])

upgrades_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛠 Улучшить клик", callback_data="mine_upgrade_click")],
    [InlineKeyboardButton(text="🖥 Купить сервер", callback_data="mine_upgrade_auto")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")]
])

grass_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌱 Посадить (100)", callback_data="grass_plant")],
    [InlineKeyboardButton(text="✂️ Собрать", callback_data="grass_harvest")],
    [InlineKeyboardButton(text="💰 Продать траву", callback_data="grass_sell")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")]
])

casino_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎲 500", callback_data="casino_500"), InlineKeyboardButton(text="🎲 5 000", callback_data="casino_5000")],
    [InlineKeyboardButton(text="🎲 10 000", callback_data="casino_10000"), InlineKeyboardButton(text="🎲 25 000", callback_data="casino_25000")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")]
])

class UserStates(StatesGroup):
    waiting_amount_usd = State(); waiting_amount_cny = State(); waiting_amount_btc = State()

HOUSES = {
    "none": ("Бездомный", 0, 0, ""), "box": ("📦 Коробка", 1000, 10, "https://images.unsplash.com/photo-1590465343632-92bc9ab4ebfa?q=80&w=800"),
    "tent": ("⛺ Палатка", 5000, 50, "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?q=80&w=800"),
    "house": ("🏠 Домик", 100000, 500, "https://images.unsplash.com/photo-1518780664697-55e3ad937233?q=80&w=800"),
    "castle": ("🏰 Замок", 15000000, 300000, "https://images.unsplash.com/photo-1533154683836-84ea7a0bc310?q=80&w=800"),
}
BUSINESSES = {
    "none": ("Без бизнеса", 0, 0, ""), "shawarma": ("🌯 Шаурма", 50000, 500, "https://images.unsplash.com/photo-1561651823-34feb02250e4?q=80&w=800"),
    "cafe": ("☕ Кофейня", 500000, 8000, "https://images.unsplash.com/photo-1554118811-1e0d58224f24?q=80&w=800"),
    "oil": ("🛢 Нефтяная вышка", 200000000, 3000000, "https://images.unsplash.com/photo-1545558014-8692077e9b5c?q=80&w=800"),
}

def get_user_game(uid):
    uid = str(uid)
    if uid not in game_data:
        game_data[uid] = {"balance": 0, "usd": 0, "cny": 0, "btc": 0.0, "level": 1, "auto_level": 0, "last_bonus": 0, "last_work": 0, "house": "none", "business": "none", "grass": 0, "last_plant": 0, "used_secret": False, "name": "Игрок"}
        save_data(GAME_FILE, game_data)
    return game_data[uid]

def get_btc_price(): return random.randint(50000, 150000)

def generate_game_text(user, name):
    rank = "🥉 Новичок" if user['balance'] < 1000 else "🥈 Стажёр" if user['balance'] < 10000 else "🥇 Опытный" if user['balance'] < 50000 else "👑 Магнат"
    h_id, b_id = user.get('house', 'none'), user.get('business', 'none')
    h_name, h_inc = HOUSES[h_id][0], HOUSES[h_id][2]
    b_name, b_inc = BUSINESSES[b_id][0], BUSINESSES[b_id][2]
    return (f"🏢 <b>Империя {name}</b>\n👑 Статус: {rank}\n\n"
            f"💰 Монеты: <b>{user['balance']}</b>\n💵 USD: <b>${user.get('usd', 0)}</b> | 💴 CNY: <b>¥{user.get('cny', 0)}</b> | 🪙 BTC: <b>₿{user.get('btc', 0.0):.4f}</b>\n\n"
            f"🏘 Жилье: {h_name} (+{h_inc}/ч)\n💼 Бизнес: {b_name} (+{b_inc}/ч)\n🌿 Травы: <b>{user.get('grass', 0)}</b> шт.\n\n"
            f"⚙️ Клик: <b>{user['level'] * 10}</b> (Ур. {user['level']})\n🖥 Авто-доход: <b>{user.get('auto_level', 0) * 5}</b> в час")

# --- САМЫЙ ГЛАВНЫЙ ОБРАБОТЧИК КНОПКИ ---
@dp.message(Command("start"))
@dp.message(F.text.contains("Майнинг-Ферма"))
async def cmd_start(message: Message):
    print(f"ПОЛУЧЕНО СООБЩЕНИЕ: {message.text}")
    user = get_user_game(message.from_user.id)
    user['name'] = message.from_user.first_name
    
    # Отправляем карточку игры (без лишних приветствий)
    try:
        await message.answer(generate_game_text(user, message.from_user.first_name), reply_markup=game_kb, parse_mode="HTML")
    except Exception as e:
        print(f"ОШИБКА ОТПРАВКИ: {e}")
        await message.answer("Ошибка сети. Попробуй выключить VPN и нажать еще раз.")

@dp.message(F.text.lower().strip() == "ямиллионер")
async def secret_millionaire(message: Message):
    user = get_user_game(message.from_user.id)
    if user.get('used_secret', False): await message.answer("Хитрец! Код можно использовать только один раз! 😉"); return
    user['balance'] += 1000000; user['used_secret'] = True; save_data(GAME_FILE, game_data)
    await message.answer_photo(photo="https://images.unsplash.com/photo-1518895949257-7621c3c786d7?q=80&w=800", caption="🎉 <b>ПАРАМ-ПАМ-ПАМ!</b> 🎉\n\nТы получил <b>1 000 000 монет</b>!", parse_mode="HTML", reply_markup=game_kb)

@dp.callback_query(F.data == "game_back")
async def game_back(callback: CallbackQuery):
    user = get_user_game(callback.from_user.id)
    try: await callback.message.edit_text(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
    except: pass
    await callback.answer()

@dp.callback_query(F.data.startswith("mine_"))
async def game_process(callback: CallbackQuery):
    action = callback.data; user = get_user_game(callback.from_user.id)
    if action == "mine_click": user['balance'] += user['level'] * 10; save_data(GAME_FILE, game_data); await callback.answer(f"⛏ +{user['level'] * 10} монет!", show_alert=False)
    elif action == "mine_upgrades": await callback.message.edit_text(f"🛠 <b>Улучшения:</b>\n\n⚙️ Сила клика: Ур. {user['level']} (Стоимость: {user['level'] * 100})\n🖥 Серверы: Ур. {user.get('auto_level', 0)} (Стоимость: {(user.get('auto_level', 0) + 1) * 500})", reply_markup=upgrades_kb, parse_mode="HTML"); await callback.answer(); return
    elif action == "mine_upgrade_click":
        cost = user['level'] * 100
        if user['balance'] >= cost: user['balance'] -= cost; user['level'] += 1; save_data(GAME_FILE, game_data); await callback.answer("🛠 Клик улучшен!", show_alert=True)
        else: await callback.answer(f"❌ Нужно {cost} монет!", show_alert=True); return
    elif action == "mine_upgrade_auto":
        cost = (user.get('auto_level', 0) + 1) * 500
        if user['balance'] >= cost: user['balance'] -= cost; user['auto_level'] = user.get('auto_level', 0) + 1; save_data(GAME_FILE, game_data); await callback.answer("🖥 Сервер куплен!", show_alert=True)
        else: await callback.answer(f"❌ Нужно {cost} монет!", show_alert=True); return
    elif action == "mine_bonus":
        now = int(time.time())
        if now - user.get('last_bonus', 0) >= 86400: bonus = 1000 + (user['level'] * 100); user['balance'] += bonus; user['last_bonus'] = now; save_data(GAME_FILE, game_data); await callback.answer(f"🎁 Бонус: +{bonus}!", show_alert=True)
        else: await callback.answer(f"⏳ Жди {(86400 - (now - user.get('last_bonus', 0))) // 3600} ч.", show_alert=True); return
    elif action == "mine_top":
        sorted_users = sorted(game_data.items(), key=lambda x: x[1]['balance'], reverse=True)[:10]
        top_text = "🏆 <b>Топ-10 Богатейших:</b>\n\n"
        for i, (u_id, u_data) in enumerate(sorted_users):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🔹"
            top_text += f"{medal} {i+1}. {u_data.get('name', 'Игрок')} — {u_data['balance']} монет\n"
        await callback.message.answer(top_text, parse_mode="HTML"); await callback.answer(); return
    if action in ["mine_click", "mine_upgrade_click", "mine_upgrade_auto", "mine_bonus"]:
        try: await callback.message.edit_text(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
        except: pass
    await callback.answer()

@dp.callback_query(F.data == "bank_menu")
async def bank_menu(callback: CallbackQuery):
    await callback.message.edit_text(f"💱 <b>Банк</b>\n\nКурсы:\n💵 1 USD = 100 монет\n💴 1 CNY = 15 монет\n🪙 1 BTC = {get_btc_price()} монет\n\nВыбери действие:", reply_markup=bank_kb, parse_mode="HTML"); await callback.answer()

@dp.callback_query(F.data == "bank_buy_usd")
async def bank_buy_usd_start(callback: CallbackQuery, state: FSMContext): await state.set_state(UserStates.waiting_amount_usd); await callback.message.answer("💵 Сколько долларов купить? Напиши число.\n/cancel - отмена"); await callback.answer()
@dp.callback_query(F.data == "bank_buy_cny")
async def bank_buy_cny_start(callback: CallbackQuery, state: FSMContext): await state.set_state(UserStates.waiting_amount_cny); await callback.message.answer("💴 Сколько юаней купить? Напиши число.\n/cancel - отмена"); await callback.answer()
@dp.callback_query(F.data == "bank_buy_btc")
async def bank_buy_btc_start(callback: CallbackQuery, state: FSMContext): await state.set_state(UserStates.waiting_amount_btc); await callback.message.answer(f"🪙 Сколько BTC купить? Напиши число.\nКурс: 1 BTC = {get_btc_price()} монет\n/cancel - отмена"); await callback.answer()

@dp.message(UserStates.waiting_amount_usd)
async def process_buy_usd(message: Message, state: FSMContext):
    if message.text.lower() == "/cancel": await state.clear(); await message.answer("Отменено.", reply_markup=main_kb); return
    try: amount = int(message.text); assert amount > 0
    except: await message.answer("❌ Ошибка. Введи целое число > 0."); return
    cost = amount * 100; user = get_user_game(message.from_user.id)
    if user['balance'] >= cost: user['balance'] -= cost; user['usd'] += amount; save_data(GAME_FILE, game_data); await state.clear(); await message.answer(f"✅ Куплено {amount} USD!", reply_markup=main_kb); await message.answer(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
    else: await message.answer(f"❌ Нужно {cost} монет!")

@dp.message(UserStates.waiting_amount_cny)
async def process_buy_cny(message: Message, state: FSMContext):
    if message.text.lower() == "/cancel": await state.clear(); await message.answer("Отменено.", reply_markup=main_kb); return
    try: amount = int(message.text); assert amount > 0
    except: await message.answer("❌ Ошибка. Введи целое число > 0."); return
    cost = amount * 15; user = get_user_game(message.from_user.id)
    if user['balance'] >= cost: user['balance'] -= cost; user['cny'] += amount; save_data(GAME_FILE, game_data); await state.clear(); await message.answer(f"✅ Куплено {amount} CNY!", reply_markup=main_kb); await message.answer(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
    else: await message.answer(f"❌ Нужно {cost} монет!")

@dp.message(UserStates.waiting_amount_btc)
async def process_buy_btc(message: Message, state: FSMContext):
    if message.text.lower() == "/cancel": await state.clear(); await message.answer("Отменено.", reply_markup=main_kb); return
    try: amount = float(message.text); assert amount > 0
    except: await message.answer("❌ Ошибка. Введи число (можно с точкой)."); return
    price = get_btc_price(); cost = int(price * amount); user = get_user_game(message.from_user.id)
    if user['balance'] >= cost: user['balance'] -= cost; user['btc'] += amount; save_data(GAME_FILE, game_data); await state.clear(); await message.answer(f"✅ Куплено {amount} BTC!", reply_markup=main_kb); await message.answer(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
    else: await message.answer(f"❌ Нужно {cost} монет!")

@dp.callback_query(F.data == "bank_sell_all")
async def process_sell(callback: CallbackQuery):
    user = get_user_game(callback.from_user.id); price = get_btc_price()
    earned = int(user.get('btc', 0.0) * price) + (user.get('usd', 0) * 90) + (user.get('cny', 0) * 13)
    if earned == 0: await callback.answer("❌ Нет валюты!", show_alert=True); return
    user['balance'] += earned; user['usd'] = 0; user['cny'] = 0; user['btc'] = 0.0; save_data(GAME_FILE, game_data)
    await callback.answer(f"💸 Продано всё за {earned}!", show_alert=True)
    try: await callback.message.edit_text(generate_game_text(user, user.get('name', 'Игрок')), reply_markup=game_kb, parse_mode="HTML")
    except: pass

@dp.callback_query(F.data == "grass_menu")
async def grass_menu(callback: CallbackQuery):
    user = get_user_game(callback.from_user.id); await callback.message.edit_text(f"🌱 <b>Ферма</b>\n\nВ инвентаре: <b>{user.get('grass', 0)}</b> шт.\nЦена: <b>300</b>/шт.\n\nПосадка: 100. Ждать: 1 мин.", reply_markup=grass_kb, parse_mode="HTML"); await callback.answer()

@dp.callback_query(F.data.startswith("grass_"))
async def grass_process(callback: CallbackQuery):
    action = callback.data; user = get_user_game(callback.from_user.id); now = int(time.time())
    if action == "grass_plant":
        if user['balance'] < 100: await callback.answer("❌ Нужно 100!", show_alert=True); return
        if now - user.get('last_plant', 0) < 60: await callback.answer("⏳ Жди минуту!", show_alert=True); return
        user['balance'] -= 100; user['last_plant'] = now; save_data(GAME_FILE, game_data); await callback.answer("🌱 Посажено!", show_alert=True)
    elif action == "grass_harvest":
        if now - user.get('last_plant', 0) < 60: await callback.answer(f"⏳ Жди {60 - (now - user.get('last_plant', 0))} сек.", show_alert=True); return
        if user.get('last_plant', 0) == 0: await callback.answer("❌ Пусто!", show_alert=True); return
        user['grass'] += 1; user['last_plant'] = 0; save_data(GAME_FILE, game_data); await callback.answer("✂️ Собрано!", show_alert=True)
    elif action == "grass_sell":
        if user.get('grass', 0) == 0: await callback.answer("❌ Нет травы!", show_alert=True); return
        earned = user['grass'] * 300; user['balance'] += earned; user['grass'] = 0; save_data(GAME_FILE, game_data); await callback.answer(f"💰 +{earned}!", show_alert=True)
    try: await callback.message.edit_text(f"🌱 <b>Ферма</b>\n\nВ инвентаре: <b>{user.get('grass', 0)}</b> шт.\nЦена: <b>300</b>/шт.\n\nПосадка: 100. Ждать: 1 мин.", reply_markup=grass_kb, parse_mode="HTML")
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "prop_menu")
async def prop_menu(callback: CallbackQuery): await callback.message.edit_text("🏘 <b>Имущество</b>\n\nВыбери:", reply_markup=prop_menu_kb, parse_mode="HTML"); await callback.answer()

@dp.callback_query(F.data == "house_menu")
async def house_menu(callback: CallbackQuery):
    user = get_user_game(callback.from_user.id); house_id = user.get('house', 'none')
    kb = [[InlineKeyboardButton(text=f"Купить {name} ({price})", callback_data=f"buy_house_{h_id}")] for h_id, (name, price, income, img) in HOUSES.items() if h_id != "none" and h_id != house_id]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="prop_menu")])
    text = f"🏘 <b>Дома</b>\n\nТвой дом: {HOUSES[house_id][0]}\n\n"
    if house_id != "none": await callback.message.answer_photo(photo=HOUSES[house_id][3], caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    else: await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_house_"))
async def buy_house(callback: CallbackQuery):
    h_id = callback.data.replace("buy_house_", ""); user = get_user_game(callback.from_user.id); name, price, income, img = HOUSES[h_id]
    if user['balance'] < price: await callback.answer(f"❌ Нужно {price}!", show_alert=True); return
    user['balance'] -= price; user['house'] = h_id; save_data(GAME_FILE, game_data); await callback.answer(f"🎉 Куплено!", show_alert=True)
    await callback.message.answer_photo(photo=img, caption=f"🏘 Твой дом: <b>{name}</b>\nДоход: +{income}/час", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="house_menu")]]), parse_mode="HTML")
    try: await callback.message.delete()
    except: pass

@dp.callback_query(F.data == "business_menu")
async def business_menu(callback: CallbackQuery):
    user = get_user_game(callback.from_user.id); b_id = user.get('business', 'none')
    kb = [[InlineKeyboardButton(text=f"Купить {name} ({price})", callback_data=f"buy_biz_{bid}")] for bid, (name, price, income, img) in BUSINESSES.items() if bid != "none" and bid != b_id]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="prop_menu")])
    text = f"💼 <b>Бизнесы</b>\n\nТвой: {BUSINESSES[b_id][0]}\n\n"
    if b_id != "none": await callback.message.answer_photo(photo=BUSINESSES[b_id][3], caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    else: await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_biz_"))
async def buy_biz(callback: CallbackQuery):
    bid = callback.data.replace("buy_biz_", ""); user = get_user_game(callback.from_user.id); name, price, income, img = BUSINESSES[bid]
    if user['balance'] < price: await callback.answer(f"❌ Нужно {price}!", show_alert=True); return
    user['balance'] -= price; user['business'] = bid; save_data(GAME_FILE, game_data); await callback.answer(f"🎉 Куплено!", show_alert=True)
    await callback.message.answer_photo(photo=img, caption=f"💼 Твой бизнес: <b>{name}</b>\nДоход: +{income}/час", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="business_menu")]]), parse_mode="HTML")
    try: await callback.message.delete()
    except: pass

@dp.callback_query(F.data == "casino_menu")
async def casino_menu(callback: CallbackQuery): await callback.message.edit_text("🎰 <b>
