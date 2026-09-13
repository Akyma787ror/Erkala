import asyncio
import os
import sys
import time
import json
import logging
import random
from datetime import datetime, timedelta

# ====== КОСТЫЛЬ ДЛЯ PYTHON 3.14 ======
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# ====== ИМПОРТЫ ======
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, CallbackQueryHandler, PreCheckoutQueryHandler
)

# ====== ЛОГИ ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("AkyBot")

# ====== ВАШИ ДАННЫЕ ======
API_ID = 35202026
API_HASH = "94c6bc97c02df79ecbb5436e29046213"
BOT_TOKEN = "8879794558:AAFL-UrzRe-BXitXtWdzzT9qi7NO2rH1Z5A"

# 👇 ТВОЙ TELEGRAM ID — только ты видишь "🔥 Прогрев"
ADMIN_ID = 7960395012

ACCOUNTS = [
    {"idx": 1,  "phone": "+959759277029", "username": "ssssss43s"},
    {"idx": 2,  "phone": "+16675666116",  "username": "fffffbbbbb43"},
    {"idx": 3,  "phone": "+959755697817", "username": "fffffff433"},
    {"idx": 4,  "phone": "+18782888424",  "username": "ffffffgggggg67"},
    {"idx": 5,  "phone": "+56954395242",  "username": None},
    {"idx": 6,  "phone": "+15673905957",  "username": None},
    {"idx": 7,  "phone": "+79036739118",  "username": "aaaaaa9924"},
    {"idx": 8,  "phone": "+14405363300",  "username": "hhhhhh6689g"},
    {"idx": 9,  "phone": "+14133937222",  "username": "bbbvvvhhh67"},
    {"idx": 10, "phone": "+13478424320",  "username": "gsssv54"},
    {"idx": 11, "phone": "+14352660735",  "username": "last632"},
]

CHATTABLE = [a for a in ACCOUNTS if a.get("username")]
ALL_ACCOUNTS = ACCOUNTS

# ===================================
#  ФРАЗЫ
# ===================================
OPENERS = [
    "Привет", "Привет!", "Хай", "Здравствуй", "Добрый день",
    "Хэй, как дела?", "Ку", "Йо", "Привет-привет", "Салют",
    "О, привет!", "Здарова", "Хай-хай", "Доброго утра", "Приветствую",
]
REPLIES = [
    "Привет", "Привет! Всё хорошо", "Привет, ты как?",
    "Здравствуй, давно не общались", "Хэй! Рад видеть",
    "О, привет! Как сам?", "Приветствую!", "Здарова!",
    "Привет-привет!", "Ку!", "Как жизнь?",
]
RESPONSES = [
    "Всё норм, ты как?", "Хорошо, спасибо!", "Отлично, а у тебя?",
    "Потихоньку", "Всё путём", "Лучше всех", "Не жалуюсь",
    "Как сам?", "Что нового?", "Чем занимаешься?",
    "Всё в порядке, а у тебя?", "Нормально, спасибо",
    "Да всё отлично!", "Как всегда на позитиве",
]
CONTINUERS = [
    "Да вот, работаю", "Отдыхаю", "Ничего особенного",
    "Планирую на выходные поехать", "Смотрю фильм сейчас",
    "Читаю книгу", "Слушаю музыку", "Готовлю ужин",
    "Учусь к экзамену", "С друзьями встречаюсь", "Сижу дома",
    "Разбираюсь с делами", "Играю в игру", "Пью кофе",
    "Гуляю по парку", "Смотрю сериал", "Дела по дому",
    "Пишу код", "Думаю о жизни", "Катаюсь на велике",
]
REACTIONS = [
    "Понятно", "Ясно", "Круто", "Класс!", "Вау", "Ничего себе",
    "Согласен", "Точно", "Ага", "Да, так и есть",
    "Интересно", "Здорово", "Молодец", "Супер!", "Огонь",
    "Красава", "Респект", "Норм", "Ок", "Good",
]
CLOSERS = [
    "Ладно, я побежал", "До связи!", "Позже напишу",
    "Давай, удачи!", "Ок, пока", "Всё, мне пора",
    "Хорошего дня!", "Спишемся ещё", "Пока-пока", "Бывай!",
    "До вечера!", "До завтра!", "Увидимся!",
]
EMOJIS = ["🔥", "😊", "👍", "❤️", "😂", "🤔", "👌", "✌️", "😎", "🙌", "✨", "💯", "🎉", "😉", "🤝"]

# ===================================
#  ГОЛОСОВЫЕ
# ===================================
VOICES_DIR = "voices"

def get_voice_files():
    if not os.path.isdir(VOICES_DIR):
        return []
    files = []
    for f in os.listdir(VOICES_DIR):
        if f.lower().endswith((".ogg", ".mp3", ".m4a", ".opus", ".wav")):
            files.append(os.path.join(VOICES_DIR, f))
    return files

# ===================================
#  ПОДПИСКИ (ПРЕМИУМ)
# ===================================
USERS_FILE = "users.json"
SPAMBLOCK_FILE = "spamblock.json"

PLANS = [
    ("promo_day", "🎉 АКЦИЯ ТОЛЬКО СЕГОДНЯ", 1, 20),
    ("day",       "Премиум на день",         1, 50),
    ("week",      "Премиум на неделю",       7, 99),
    ("month",     "Премиум на месяц",        30, 199),
]

# ====== ГЛОБАЛЬНЫЕ ФЛАГИ ======
stop_spam_flag = False
stop_warmup_flag = False
warmup_running = False

WARMUP_INTERVAL = 3 * 60 * 60   # 3 часа

# ====== СПАМ-БЛОК ======
def load_spamblock():
    if os.path.exists(SPAMBLOCK_FILE):
        try:
            with open(SPAMBLOCK_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_spamblock(blocked: set):
    with open(SPAMBLOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(list(blocked), f, ensure_ascii=False, indent=2)

spamblock_accounts = load_spamblock()


# ===================================
#  РАБОТА С ПОЛЬЗОВАТЕЛЯМИ
# ===================================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id), {
        "free_used": False,
        "free_runs": 0,
        "sub_until": None,
        "total_stars": 0
    })

def update_user(user_id, data):
    users = load_users()
    users[str(user_id)] = data
    save_users(users)

def is_sub_active(user):
    sub_until = user.get("sub_until")
    if not sub_until:
        return False
    try:
        return datetime.fromisoformat(sub_until) > datetime.now()
    except:
        return False

def sub_time_left(user):
    sub_until = user.get("sub_until")
    if not sub_until:
        return None
    try:
        end = datetime.fromisoformat(sub_until)
        delta = end - datetime.now()
        if delta.total_seconds() <= 0:
            return None
        d, h, m = delta.days, delta.seconds // 3600, (delta.seconds % 3600) // 60
        if d > 0:   return f"{d} дн. {h} ч."
        if h > 0:   return f"{h} ч. {m} мин."
        return f"{m} мин."
    except:
        return None

def add_subscription(user_id, days):
    user = get_user(user_id)
    now = datetime.now()
    if is_sub_active(user):
        try:
            base = datetime.fromisoformat(user["sub_until"])
        except:
            base = now
    else:
        base = now
    new_until = base + timedelta(days=days)
    user["sub_until"] = new_until.isoformat()
    update_user(user_id, user)
    return new_until

def can_use_bot(user_id):
    user = get_user(user_id)
    if is_sub_active(user):           return True, "active"
    if user.get("free_runs", 0) > 0:  return True, "bonus"
    if not user.get("free_used"):     return True, "free"
    return False, "no_sub"

def use_free_run(user_id):
    user = get_user(user_id)
    if user.get("free_runs", 0) > 0:
        user["free_runs"] -= 1
        update_user(user_id, user)
        return True
    return False

def mark_free_used(user_id):
    user = get_user(user_id)
    user["free_used"] = True
    update_user(user_id, user)


# ===================================
#  РЕАЛИСТИЧНЫЕ ПАУЗЫ
# ===================================
async def human_typing(client, peer, min_len=10, max_len=60):
    length = random.randint(min_len, max_len)
    duration = length * random.uniform(0.05, 0.1)
    duration = min(max(duration, 1.5), 12)
    try:
        await client.send_chat_action(peer, "typing")
    except:
        pass
    await asyncio.sleep(duration)

async def read_messages(client, peer):
    try:
        async for _ in client.get_chat_history(peer, limit=1):
            break
    except:
        pass


# ===================================
#  ОТПРАВКА
# ===================================
async def send_text(client, peer, text):
    await human_typing(client, peer, min_len=len(text), max_len=len(text) + 20)
    return await client.send_message(peer, text)

async def send_voice(client, peer, voice_files):
    if voice_files and random.random() < 0.7:
        try:
            vf = random.choice(voice_files)
            await client.send_chat_action(peer, "record_audio")
            await asyncio.sleep(random.uniform(2, 6))
            return await client.send_voice(peer, vf)
        except Exception as e:
            log.warning(f"Не отправилось голосовое: {e}")
    fake_dur = random.randint(5, 25)
    return await send_text(client, peer, f"🎤 Голосовое ({fake_dur} сек)")

async def send_sticker(client, peer):
    try:
        sets = await client.get_sticker_sets() if hasattr(client, 'get_sticker_sets') else None
        if sets:
            s = random.choice(sets)
            stickers = await client.get_stickers(s.set_name)
            if stickers:
                st = random.choice(stickers)
                return await client.send_sticker(peer, st.file_id)
    except Exception:
        pass
    return None

async def send_reaction(client, peer, msg_id, emoji=None):
    try:
        em = emoji or random.choice(["👍", "🔥", "❤️", "😂", "🎉", "🤔", "💯"])
        await client.send_reaction(peer, msg_id, em)
        return True
    except:
        return False


# ===================================
#  ПРОВЕРКА СПАМ-БЛОКА
# ===================================
async def check_spamblock(client, sender_username, recipient_username):
    try:
        msg = await client.send_message(f"@{recipient_username}", ".")
        await asyncio.sleep(random.uniform(0.4, 1.0))
        try:
            await client.delete_messages(f"@{recipient_username}", msg.id)
        except:
            pass
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return None
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ["peer", "spam", "blocked", "flood", "privacy"]):
            return False
        return None


# ===================================
#  ДИАЛОГ
# ===================================
async def realistic_conversation(client_a, acc_a, client_b, acc_b, voice_files):
    ua = acc_a["username"]
    ub = acc_b["username"]

    a_blocked = ua in spamblock_accounts
    b_blocked = ub in spamblock_accounts

    if a_blocked and not b_blocked:
        initiator_client, initiator_u = client_b, ub
        responder_client, responder_u = client_a, ua
        log.info(f"   ℹ️ @{ub} (свободный) → @{ua} (в блоке)")
    elif b_blocked and not a_blocked:
        initiator_client, initiator_u = client_a, ua
        responder_client, responder_u = client_b, ub
        log.info(f"   ℹ️ @{ua} (свободный) → @{ub} (в блоке)")
    elif a_blocked and b_blocked:
        log.warning(f"   ⚠️ Оба в блоке: @{ua} ↔ @{ub} — пропуск")
        return False, "both_blocked"
    else:
        initiator_client, initiator_u = client_a, ua
        responder_client, responder_u = client_b, ub

    try:
        opener = random.choice(OPENERS)
        try:
            msg1 = await send_text(initiator_client, f"@{responder_u}", opener)
            log.info(f"   💬 @{initiator_u} → @{responder_u}: {opener}")
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["peer", "spam", "blocked", "privacy"]):
                spamblock_accounts.add(initiator_u)
                save_spamblock(spamblock_accounts)
                log.warning(f"   🚫 @{initiator_u} в спам-блок")
                return False, "initiator_blocked"
            raise

        await asyncio.sleep(random.uniform(3, 15))
        await read_messages(responder_client, f"@{initiator_u}")

        reply = random.choice(REPLIES)
        try:
            msg2 = await send_text(responder_client, f"@{initiator_u}", reply)
            log.info(f"   💬 @{responder_u} → @{initiator_u}: {reply}")
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["peer", "spam", "blocked", "privacy"]):
                spamblock_accounts.add(responder_u)
                save_spamblock(spamblock_accounts)
                log.warning(f"   🚫 @{responder_u} не может отвечать")
                return False, "responder_blocked"
            raise

        if random.random() < 0.4:
            await send_reaction(responder_client, f"@{initiator_u}", msg1.id)

        r = random.random()
        if r < 0.25:
            await asyncio.sleep(random.uniform(3, 8))
            await send_voice(initiator_client, f"@{responder_u}", voice_files)
            log.info(f"   🎤 @{initiator_u}: голосовое")
        elif r < 0.40:
            await asyncio.sleep(random.uniform(2, 6))
            st = await send_sticker(initiator_client, f"@{responder_u}")
            if st:
                log.info(f"   🎨 @{initiator_u}: стикер")
            else:
                resp = random.choice(RESPONSES)
                await send_text(initiator_client, f"@{responder_u}", resp)
                log.info(f"   💬 @{initiator_u}: {resp}")
        else:
            resp = random.choice(RESPONSES)
            await send_text(initiator_client, f"@{responder_u}", resp)
            log.info(f"   💬 @{initiator_u} → @{responder_u}: {resp}")

        await asyncio.sleep(random.uniform(4, 12))
        await read_messages(responder_client, f"@{initiator_u}")

        cont = random.choice(CONTINUERS)
        await send_text(responder_client, f"@{initiator_u}", cont)
        log.info(f"   💬 @{responder_u} → @{initiator_u}: {cont}")

        await asyncio.sleep(random.uniform(3, 10))

        react = random.choice(REACTIONS) + " " + random.choice(EMOJIS)
        await send_text(initiator_client, f"@{responder_u}", react)
        log.info(f"   💬 @{initiator_u} → @{responder_u}: {react}")

        if random.random() < 0.5:
            await send_reaction(initiator_client, f"@{responder_u}", msg2.id)

        if random.random() < 0.6:
            await asyncio.sleep(random.uniform(5, 15))
            closer = random.choice(CLOSERS)
            await send_text(responder_client, f"@{initiator_u}", closer)
            log.info(f"   💬 @{responder_u} → @{initiator_u}: {closer}")

        log.info(f"   ✅ Диалог @{ua} ↔ @{ub} завершён")
        return True, "ok"

    except FloodWait as e:
        log.warning(f"   ⏳ FloodWait {e.value} сек")
        await asyncio.sleep(e.value)
        return False, "flood"
    except Exception as e:
        log.error(f"   ⚠️ Ошибка диалога @{ua} ↔ @{ub}: {e}")
        return False, "error"


# ===================================
#  ПРОГРЕВ
# ===================================
async def warmup_accounts(round_num):
    global warmup_running, spamblock_accounts
    warmup_running = True

    log.info("=" * 55)
    log.info(f"🔥 ПРОГРЕВ #{round_num} | Аккаунтов: {len(CHATTABLE)}")
    log.info("=" * 55)

    if len(CHATTABLE) < 2:
        log.warning("⚠️ Нужно минимум 2 аккаунта")
        warmup_running = False
        return 0

    clients = {}
    for acc in CHATTABLE:
        if stop_warmup_flag:
            break
        try:
            c = Client(
                name=f"account_{acc['idx']}",
                api_id=API_ID,
                api_hash=API_HASH,
                phone_number=acc["phone"],
                workdir="sessions"
            )
            await c.start()
            me = await c.get_me()
            clients[acc["username"]] = (c, acc)
            log.info(f"✅ @{acc['username']} — {me.first_name}")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            log.error(f"❌ @{acc['username']}: {e}")

    if len(clients) < 2:
        log.warning("⚠️ Недостаточно аккаунтов")
        for u, (c, _) in clients.items():
            try: await c.stop()
            except: pass
        warmup_running = False
        return 0

    voice_files = get_voice_files()
    if voice_files:
        log.info(f"🎤 Голосовых: {len(voice_files)}")

    log.info("\n🚫 Проверка спам-блока...")
    usernames = list(clients.keys())
    test_target = usernames[0]
    for u in usernames:
        if u == test_target:
            continue
        c, _ = clients[u]
        result = await check_spamblock(c, u, test_target)
        if result is False:
            if u not in spamblock_accounts:
                spamblock_accounts.add(u)
                log.warning(f"   🚫 @{u} — в спам-блоке")
        elif result is True:
            if u in spamblock_accounts:
                spamblock_accounts.discard(u)
                log.info(f"   ✅ @{u} — вышел из блока")
        await asyncio.sleep(random.uniform(1, 2))

    save_spamblock(spamblock_accounts)

    free = [u for u in usernames if u not in spamblock_accounts]
    blocked = [u for u in usernames if u in spamblock_accounts]
    random.shuffle(free)
    random.shuffle(blocked)

    pairs = []
    while free and blocked:
        pairs.append((free.pop(0), blocked.pop(0)))
    while len(free) >= 2:
        pairs.append((free.pop(0), free.pop(0)))

    leftover = free + blocked

    log.info(f"\n💬 Пар: {len(pairs)} | Одиночек: {len(leftover)}")
    log.info("=" * 55)

    pairs_count = 0
    for a, b in pairs:
        if stop_warmup_flag:
            break
        c_a, acc_a = clients[a]
        c_b, acc_b = clients[b]
        ok, status = await realistic_conversation(c_a, acc_a, c_b, acc_b, voice_files)
        if ok:
            pairs_count += 1
        pause = random.uniform(8, 20)
        log.info(f"   ⏸️ Пауза {pause:.1f} сек")
        await asyncio.sleep(pause)

    if leftover and not stop_warmup_flag:
        for lonely in leftover:
            if lonely in spamblock_accounts:
                free_now = [u for u in usernames if u not in spamblock_accounts and u != lonely]
                if free_now:
                    sender = random.choice(free_now)
                    c_s, _ = clients[sender]
                    try:
                        await send_text(c_s, f"@{lonely}", random.choice(OPENERS))
                        log.info(f"   💬 @{sender} → @{lonely} (спасение)")
                    except: pass
            else:
                targets = [u for u in usernames if u != lonely]
                if targets:
                    target = random.choice(targets)
                    c_l, _ = clients[lonely]
                    try:
                        await send_text(c_l, f"@{target}", random.choice(OPENERS))
                        log.info(f"   💬 @{lonely} → @{target} (одиночка)")
                    except: pass

    for u, (c, _) in clients.items():
        try: await c.stop()
        except: pass

    log.info(f"\n✅ ПРОГРЕВ #{round_num} завершён. Диалогов: {pairs_count}")
    warmup_running = False
    return pairs_count


# ===================================
#  ПЛАНИРОВЩИК
# ===================================
async def warmup_scheduler():
    log.info("⏰ Планировщик прогрева запущен (каждые 3 часа)")
    await asyncio.sleep(20)
    cycle = 0
    while not stop_warmup_flag:
        cycle += 1
        if warmup_running:
            await asyncio.sleep(30)
            continue
        log.info(f"\n🔥 ПЛАНОВЫЙ ПРОГРЕВ #{cycle} | {time.strftime('%H:%M:%S')}")
        try:
            await warmup_accounts(round_num=f"auto#{cycle}")
        except Exception as e:
            log.error(f"❌ Ошибка прогрева: {e}")
        log.info("⏰ Следующий прогрев через 3 часа")
        waited = 0
        while waited < WARMUP_INTERVAL:
            if stop_warmup_flag:
                return
            await asyncio.sleep(10)
            waited += 10


# ===================================
#  СПАМ
# ===================================
async def send_message_and_delete_instant(phone_number, session_name, chat_id, message, round_num, premium=False):
    while warmup_running:
        await asyncio.sleep(5)

    app = Client(
        name=session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone_number,
        workdir="sessions"
    )
    try:
        await app.start()
        me = await app.get_me()
        log.info(f"✅ [{round_num}] {phone_number} ({me.first_name})")

        sent = await app.send_message(chat_id, message)
        log.info(f"📤 [{round_num}] {phone_number}: Отправлено")

        try: await app.delete_messages(chat_id, sent.id)
        except: pass
        try: await app.delete_dialog(chat_id)
        except:
            try: await app.leave_chat(chat_id)
            except: pass
        return True

    except FloodWait as e:
        log.warning(f"⏳ [{round_num}] {phone_number}: FloodWait {e.value}")
        await asyncio.sleep(e.value)
        try:
            s = await app.send_message(chat_id, message)
            try: await app.delete_messages(chat_id, s.id)
            except: pass
            try: await app.delete_dialog(chat_id)
            except: pass
            return True
        except: return False

    except Exception as e:
        log.error(f"❌ [{round_num}] {phone_number}: {e}")
        return False

    finally:
        try: await app.stop()
        except: pass

async def send_one_round(chat_id, message, round_num, premium=False):
    global stop_spam_flag
    tasks = []
    for acc in ALL_ACCOUNTS:
        if stop_spam_flag:
            break
        tasks.append(send_message_and_delete_instant(
            acc["phone"], f"account_{acc['idx']}", chat_id, message, round_num, premium
        ))
    if not tasks:
        return 0
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for r in results if r is True)

async def start_spam_timer(chat_id, message, duration_minutes, premium=False):
    global stop_spam_flag
    stop_spam_flag = False
    duration_seconds = duration_minutes * 60
    start_time = time.time()
    round_num = 0
    total_success = 0
    total_attempts = 0

    mode = "ПРЕМИУМ ⚡" if premium else "обычный"
    log.info(f"\n🔥 СПАМ [{mode}]: {chat_id} | {duration_minutes} мин")
    log.info("=" * 55)

    while True:
        if stop_spam_flag: break
        if time.time() - start_time >= duration_seconds: break

        while warmup_running and not stop_spam_flag:
            log.info("⏸️ Спам ждёт прогрев...")
            await asyncio.sleep(5)
        if stop_spam_flag: break

        round_num += 1
        log.info(f"\n🔄 КРУГ {round_num}")

        success = await send_one_round(chat_id, message, round_num, premium)
        total_success += success
        total_attempts += len(ALL_ACCOUNTS)
        log.info(f"📊 Круг {round_num}: {success}/{len(ALL_ACCOUNTS)}")

        await asyncio.sleep(0.1 if premium else 0.3)

    log.info(f"\n✅ СПАМ ЗАВЕРШЁН: {total_success}/{total_attempts}")
    return total_success, total_attempts, round_num


# ===================================
#  МЕНЮ
# ===================================
def main_menu_keyboard(user_id):
    user = get_user(user_id)
    kb = [[InlineKeyboardButton("🚀 Запустить спам", callback_data="start_spam")]]
    if not is_sub_active(user) and user.get("free_used") and user.get("free_runs", 0) == 0:
        kb.append([InlineKeyboardButton("💎 Купить Премиум", callback_data="buy_sub")])
    else:
        kb.append([InlineKeyboardButton("💎 Премиум", callback_data="buy_sub")])

    # 🔥 Прогрев — ТОЛЬКО для админа
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton("🔥 Прогреть сейчас (ADMIN)", callback_data="warmup_now")])

    kb.append([InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")])
    kb.append([InlineKeyboardButton("⏹️ Остановить спам", callback_data="stop_spam")])
    return InlineKeyboardMarkup(kb)

def plans_keyboard(user_id):
    kb = []
    for plan in PLANS:
        code, name, days, stars = plan[0], plan[1], plan[2], plan[3]
        kb.append([InlineKeyboardButton(
            f"💎 {name} — {stars} ⭐",
            callback_data=f"buy_{code}"
        )])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def profile_text(user_id):
    user = get_user(user_id)
    txt = f"👤 *Ваш профиль*\n\n🆔 ID: `{user_id}`\n\n"
    if is_sub_active(user):
        txt += f"💎 *Премиум активен*\n⏰ Осталось: {sub_time_left(user)}\n\n"
    else:
        txt += f"❌ *Премиум не активен*\n\n"
    if not user.get("free_used"):
        txt += "🎁 Бесплатный запуск: доступен\n"
    else:
        txt += "🎁 Бесплатный запуск: использован\n"
    txt += f"\n⭐ Всего куплено звёзд: {user.get('total_stars', 0)}\n"
    return txt


# ===================================
#  СЕКРЕТНАЯ КОМАНДА /ec
# ===================================
async def secret_ec(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    user["free_runs"] = user.get("free_runs", 0) + 3
    update_user(user_id, user)
    await update.message.reply_text(
        f"✅ Активировано: *3 бесплатных запуска*\n\n"
        f"У тебя теперь: *{user['free_runs']}* бонусных запусков.",
        parse_mode="Markdown"
    )


# ===================================
#  СЕКРЕТНАЯ КОМАНДА /spam (статус спам-блока)
# ===================================
async def secret_spam_status(update: Update, context: CallbackContext):
    """Проверяет каждый аккаунт: может ли он писать ПЕРВЫМ другим аккаунтам."""
    user_id = update.effective_user.id
    log.info(f"🔍 /spam вызван user_id={user_id}")

    msg = await update.message.reply_text("🔍 Проверяю каждый аккаунт на спам-блок...")

    clients = {}
    for acc in CHATTABLE:
        try:
            c = Client(
                name=f"account_{acc['idx']}",
                api_id=API_ID,
                api_hash=API_HASH,
                phone_number=acc["phone"],
                workdir="sessions"
            )
            await c.start()
            clients[acc["username"]] = (c, acc)
            await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            log.error(f"❌ @{acc['username']}: {e}")

    if len(clients) < 2:
        await msg.edit_text("❌ Не удалось подключить достаточно аккаунтов")
        return

    usernames = list(clients.keys())

    free_list = []
    blocked_list = []
    other_list = []

    for i, u in enumerate(usernames):
        c, _ = clients[u]

        targets_to_try = [t for t in usernames if t != u]
        random.shuffle(targets_to_try)

        result = "unknown"
        for t in targets_to_try[:3]:
            try:
                m = await c.send_message(f"@{t}", ".")
                await asyncio.sleep(0.4)
                try:
                    await c.delete_messages(f"@{t}", m.id)
                except: pass
                result = "ok"
                break
            except FloodWait as e:
                await asyncio.sleep(e.value)
                result = "flood"
            except Exception as e:
                err = str(e).lower()
                if any(x in err for x in ["peer", "spam", "blocked", "privacy"]):
                    result = "blocked"
                else:
                    result = "error"
            await asyncio.sleep(0.3)

        if result == "ok":
            free_list.append(u)
            spamblock_accounts.discard(u)
        elif result == "blocked":
            blocked_list.append(u)
            spamblock_accounts.add(u)
        else:
            other_list.append((u, result))

    save_spamblock(spamblock_accounts)

    text = "🔍 *СТАТУС СПАМ-БЛОКА*\n\n"

    if free_list:
        text += f"✅ *Свободны ({len(free_list)}):*\n"
        for u in free_list:
            text += f"   ✅ @{u}\n"
        text += "\n"

    if blocked_list:
        text += f"🚫 *В спам-блоке ({len(blocked_list)}):*\n"
        for u in blocked_list:
            text += f"   🚫 @{u}\n"
        text += "\n"

    if other_list:
        text += f"⚠️ *Не удалось определить ({len(other_list)}):*\n"
        for u, status in other_list:
            text += f"   ⚠️ @{u} — {status}\n"
        text += "\n"

    text += f"📊 Всего проверено: {len(usernames)} аккаунтов"

    await msg.edit_text(text, parse_mode="Markdown")

    for u, (c, _) in clients.items():
        try: await c.stop()
        except: pass


# ===================================
#  КОМАНДЫ
# ===================================
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)

    free_status = "✅ доступен" if not user.get("free_used") else "❌ использован"
    sub_status = "✅ активна" if is_sub_active(user) else "❌ не активна"

    text = (
        "🤖 *Aky Spam Bot*\n\n"
        f"📝 Аккаунтов: {len(ALL_ACCOUNTS)}\n"
        f"💬 В переписке: {len(CHATTABLE)}\n\n"
        f"🎁 Бесплатный запуск: {free_status}\n"
        f"💎 Премиум: {sub_status}\n\n"
        "⚡ Мгновенное удаление сообщений\n"
        "🔥 Автопрогрев каждые 3 часа\n\n"
        "💎 *Премиум тарифы:*\n"
        "• 🎉 АКЦИЯ ТОЛЬКО СЕГОДНЯ — 20 ⭐\n"
        "• Премиум на день — 50 ⭐\n"
        "• Премиум на неделю — 99 ⭐\n"
        "• Премиум на месяц — 199 ⭐\n\n"
        "♾️ Безлимитный спам\n"
        "⚡ Улучшенный режим (быстрее, антидетект)\n\n"
        "🔥 *Акция 20⭐ скоро закончится! Успей купить!*"
    )

    await update.message.reply_text(text, reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")

async def button_handler(update: Update, context: CallbackContext):
    global stop_spam_flag
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = update.effective_user.id

    if data == "back":
        await q.edit_message_text("🤖 *Aky Spam Bot*\n\nВыберите действие:",
                                  reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")
    elif data == "my_profile":
        await q.edit_message_text(profile_text(user_id), parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]))
    elif data == "buy_sub":
        await q.edit_message_text(
            "💎 *Премиум подписка*\n\n"
            "🎯 Что входит:\n"
            "• ♾️ Безлимитный спам\n"
            "• ⚡ Улучшенный спам (умные паузы, антидетект)\n"
            "• 🔥 Приоритетная очередь\n"
            "• 🚀 Максимальная скорость\n\n"
            "🔥 *АКЦИЯ ТОЛЬКО СЕГОДНЯ:* Премиум-день за 20⭐!\n"
            "⏰ Успей купить — завтра будет дороже!",
            reply_markup=plans_keyboard(user_id),
            parse_mode="Markdown"
        )
    elif data == "warmup_now":
        if user_id != ADMIN_ID:
            await q.answer("❌ Недоступно", show_alert=True)
            return
        if warmup_running:
            await q.edit_message_text("🔥 Прогрев уже идёт...")
            return
        await q.edit_message_text("🔥 Запускаю прогрев...")
        await warmup_accounts(round_num="manual")
        await q.message.reply_text("✅ Прогрев завершён!")
    elif data.startswith("buy_"):
        code = data.replace("buy_", "")
        plan = next((p for p in PLANS if p[0] == code), None)
        if not plan:
            await q.edit_message_text("❌ Тариф не найден")
            return

        code, name, days, stars = plan[0], plan[1], plan[2], plan[3]

        prices = [LabeledPrice("Подписка", int(stars))]
        try:
            await q.message.reply_invoice(
                title=f"Подписка {name}",
                description=f"Премиум доступ на {days} дн.",
                payload=f"sub_{code}_{user_id}",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="sub",
                need_name=False, need_phone_number=False, need_email=False,
                need_shipping_address=False, is_flexible=False,
            )
            await q.edit_message_text(
                f"💎 Счёт на *{name}* отправлен!\n\n"
                f"💰 Стоимость: *{stars} ⭐*\n"
                f"♾️ Безлимитный спам\n"
                f"⚡ Улучшенный режим\n\n"
                f"👉 Оплатите в сообщении выше.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await q.edit_message_text(f"❌ Ошибка создания счёта: {e}")
    elif data == "start_spam":
        can, reason = can_use_bot(user_id)
        if not can:
            await q.edit_message_text(
                "❌ *Нет доступа!*\n\nБесплатный запуск уже использован.\nКупите Премиум.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Купить Премиум", callback_data="buy_sub")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
                ])
            )
            return
        context.user_data['reason'] = reason
        context.user_data['action'] = 'waiting_for_message'
        await q.edit_message_text("💬 *Шаг 1/3:* Введите текст сообщения.", parse_mode="Markdown")
    elif data == "stop_spam":
        stop_spam_flag = True
        await q.edit_message_text("🛑 ОСТАНОВКА СПАМА ОТПРАВЛЕНА")

async def handle_message(update: Update, context: CallbackContext):
    action = context.user_data.get('action')
    user_id = update.effective_user.id

    if not action:
        await start(update, context)
        return

    text = update.message.text.strip() if update.message.text else ""

    if action == 'waiting_for_message':
        context.user_data['message'] = text
        context.user_data['action'] = 'waiting_for_target'
        await update.message.reply_text("🎯 *Шаг 2/3:* Введите цель (@username / ID).", parse_mode="Markdown")
    elif action == 'waiting_for_target':
        context.user_data['target'] = text
        context.user_data['action'] = 'waiting_for_time'
        await update.message.reply_text("⏱️ *Шаг 3/3:* Введите время в минутах (0.5 — 60).", parse_mode="Markdown")
    elif action == 'waiting_for_time':
        try:
            duration = float(text.replace(',', '.'))
            if duration < 0.5: duration = 0.5
            if duration > 60:  duration = 60
        except ValueError:
            await update.message.reply_text("❌ Введите число!")
            return

        message = context.user_data.get('message')
        target = context.user_data.get('target')
        reason = context.user_data.get('reason', '')

        if reason == "bonus": use_free_run(user_id)
        elif reason == "free": mark_free_used(user_id)

        premium = (reason == "active")

        kb = [[InlineKeyboardButton("⏹️ Остановить спам", callback_data="stop_spam")]]
        note = {"bonus": "🎁 Бонусный запуск", "free": "🎁 Бесплатный запуск"}.get(reason, "💎 Премиум активен ⚡")

        await update.message.reply_text(
            f"🚀 *ЗАПУСК СПАМА!*\n\nАккаунтов: {len(ALL_ACCOUNTS)}\nЦель: `{target}`\n"
            f"Сообщение: {message[:50]}\n⏱️ Время: {duration} мин\n\n{note}",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

        success, total, rounds = await start_spam_timer(target, message, duration, premium)

        await update.message.reply_text(
            f"✅ *СПАМ ЗАВЕРШЁН!*\n\n📊 {success}/{total}\n🎯 Цель: `{target}`\n🔄 Кругов: {rounds}",
            parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id)
        )
        context.user_data.clear()


# ===================================
#  ОПЛАТА STARS
# ===================================
async def pre_checkout(update: Update, context: CallbackContext):
    q = update.pre_checkout_query
    if q.invoice_payload.startswith("sub_"):
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Ошибка счёта")

async def successful_payment(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    try:
        parts = payload.split("_")
        code = "_".join(parts[1:-1])
        plan = next((p for p in PLANS if p[0] == code), None)
        if not plan:
            await update.message.reply_text("❌ Тариф не найден")
            return

        code, name, days, stars = plan[0], plan[1], plan[2], plan[3]

        new_until = add_subscription(user_id, days)
        user = get_user(user_id)
        user["total_stars"] = user.get("total_stars", 0) + stars
        update_user(user_id, user)

        left = sub_time_left(get_user(user_id))
        await update.message.reply_text(
            f"✅ *Оплата получена!*\n\n"
            f"💎 Тариф: *{name}*\n"
            f"⭐ Оплачено: *{stars} звёзд*\n"
            f"⏰ До: `{new_until.strftime('%d.%m.%Y %H:%M')}`\n"
            f"⏳ Осталось: {left}\n\n"
            f"♾️ Безлимитный спам активен!\n"
            f"⚡ Улучшенный режим включён!",
            parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка активации: {e}")


# ===================================
#  ЗАПУСК
# ===================================
def run_bot():
    log.info("🤖 Запуск Aky Spam Bot...")
    log.info(f"📝 Аккаунтов: {len(ALL_ACCOUNTS)} | В переписке: {len(CHATTABLE)}")
    log.info(f"🚫 Спам-блок при старте: {len(spamblock_accounts)}")
    log.info(f"👤 ADMIN_ID: {ADMIN_ID}")
    log.info("💎 Тарифы:")
    for plan in PLANS:
        log.info(f"   • {plan[1]} — {plan[3]} ⭐")
    log.info("⏰ Автопрогрев каждые 3 часа")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ec", secret_ec))
    app.add_handler(CommandHandler("spam", secret_spam_status))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    loop = asyncio.get_event_loop()
    loop.create_task(warmup_scheduler())

    log.info("🚀 Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    if not CHATTABLE:
        log.error("⚠️ Нет аккаунтов с username!")
        exit()
    run_bot()