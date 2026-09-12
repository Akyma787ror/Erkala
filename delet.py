import asyncio
import os
import sys
import time
import json
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

# ====== ВАШИ ДАННЫЕ ======
API_ID = 35202026
API_HASH = "94c6bc97c02df79ecbb5436e29046213"
BOT_TOKEN = "8985038616:AAHlsm1x2DSNSEAr79-Uq9twtWHLu708Vok"

PHONE_NUMBERS = [
    "+959759277029",
    "+16675666116",
    "+959755697817",
    "+18782888424",
    "+56954395242",
    "+15673905957",
    "+79036739118",
    "+14405363300",
    "+14133937222",
    "+13478424320",
    "+14352660735"
]

# ===================================
#  ФАЙЛ ПОДПИСОК
# ===================================
USERS_FILE = "users.json"

PLANS = [
    ("day",   "1 день",   1, 50),
    ("3days", "3 дня",    3, 100),
    ("week",  "Неделя",   7, 200),
]

# ===================================
#  ГЛОБАЛЬНЫЕ ФЛАГИ
# ===================================
stop_spam_flag = False

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
        end = datetime.fromisoformat(sub_until)
        return end > datetime.now()
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
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        if days > 0:
            return f"{days} дн. {hours} ч."
        elif hours > 0:
            return f"{hours} ч. {minutes} мин."
        else:
            return f"{minutes} мин."
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
    if is_sub_active(user):
        return True, "active"
    if user.get("free_runs", 0) > 0:
        return True, "bonus"
    if not user.get("free_used"):
        return True, "free"
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
#  СПАМ
# ===================================
async def send_message_and_delete_instant(phone_number, session_name, chat_id, message, round_num):
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
        print(f"✅ [{round_num}] {phone_number} ({me.first_name})")

        sent = await app.send_message(chat_id, message)
        print(f"📤 [{round_num}] {phone_number}: Отправлено")

        try:
            await app.delete_messages(chat_id, sent.id)
        except: pass
        try:
            await app.delete_dialog(chat_id)
        except:
            try: await app.leave_chat(chat_id)
            except: pass

        return True

    except FloodWait as e:
        print(f"⏳ [{round_num}] {phone_number}: Ждём {e.value} сек")
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
        print(f"❌ [{round_num}] {phone_number}: {e}")
        return False

    finally:
        try: await app.stop()
        except: pass

async def send_one_round(chat_id, message, phone_numbers, round_num):
    global stop_spam_flag
    tasks = []
    for idx, phone in enumerate(phone_numbers, 1):
        if stop_spam_flag:
            break
        tasks.append(send_message_and_delete_instant(phone, f"account_{idx}", chat_id, message, round_num))
    if not tasks:
        return 0
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for r in results if r is True)

async def start_spam_timer(chat_id, message, phone_numbers, duration_minutes):
    global stop_spam_flag
    stop_spam_flag = False
    duration_seconds = duration_minutes * 60
    start_time = time.time()
    round_num = 0
    total_success = 0
    total_attempts = 0

    print(f"\n🔥 СПАМ: {chat_id} на {duration_minutes} мин")
    print("=" * 50)

    while True:
        if stop_spam_flag: break
        if time.time() - start_time >= duration_seconds: break

        round_num += 1
        print(f"\n🔄 КРУГ {round_num}")

        success = await send_one_round(chat_id, message, phone_numbers, round_num)
        total_success += success
        total_attempts += len(phone_numbers)
        print(f"📊 Круг {round_num}: {success}/{len(phone_numbers)}")

        await asyncio.sleep(0.3)

    print(f"\n✅ СПАМ ЗАВЕРШЁН: {total_success}/{total_attempts}")
    return total_success, total_attempts, round_num

# ===================================
#  МЕНЮ
# ===================================
def main_menu_keyboard(user_id):
    user = get_user(user_id)
    kb = [
        [InlineKeyboardButton("🚀 Запустить спам", callback_data="start_spam")],
    ]
    if not is_sub_active(user) and user.get("free_used") and user.get("free_runs", 0) == 0:
        kb.append([InlineKeyboardButton("💎 Купить подписку", callback_data="buy_sub")])
    else:
        kb.append([InlineKeyboardButton("💎 Продлить подписку", callback_data="buy_sub")])
    kb.append([InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")])
    kb.append([InlineKeyboardButton("⏹️ Остановить спам", callback_data="stop_spam")])
    return InlineKeyboardMarkup(kb)

def plans_keyboard():
    kb = []
    for code, name, days, stars in PLANS:
        kb.append([InlineKeyboardButton(
            f"💎 {name} — {stars} ⭐",
            callback_data=f"buy_{code}"
        )])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def profile_text(user_id):
    user = get_user(user_id)
    free_used = user.get("free_used", False)
    total_stars = user.get("total_stars", 0)

    txt = f"👤 *Ваш профиль*\n\n"
    txt += f"🆔 ID: `{user_id}`\n\n"

    if is_sub_active(user):
        left = sub_time_left(user)
        txt += f"💎 *Подписка активна*\n"
        txt += f"⏰ Осталось: {left}\n\n"
    else:
        txt += f"❌ *Подписка не активна*\n\n"

    if not free_used:
        txt += f"🎁 *Бесплатный запуск:* доступен (1 раз)\n\n"
    else:
        txt += f"🎁 Бесплатный запуск: использован\n\n"

    txt += f"⭐ Всего куплено звёзд: {total_stars}\n"
    return txt

# ===================================
#  СЕКРЕТНАЯ КОМАНДА /ec (работает у всех, никто не знает)
# ===================================
async def secret_ec(update: Update, context: CallbackContext):
    """Секретная команда — выдаёт 3 бонусных запуска. Нигде не упоминается."""
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
#  КОМАНДЫ
# ===================================
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)

    free_status = "✅ доступен" if not user.get("free_used") else "❌ использован"
    sub_status = "✅ активна" if is_sub_active(user) else "❌ не активна"

    text = (
        "🤖 *Aky Spam Bot*\n\n"
        f"📝 Аккаунтов в базе: {len(PHONE_NUMBERS)}\n\n"
        f"🎁 Бесплатный запуск: {free_status}\n"
        f"💎 Подписка: {sub_status}\n\n"
        "⚡ Мгновенное удаление сообщений\n"
        "🔄 Спам по времени\n\n"
        "*Тарифы:*\n"
        "• 1 день — 50 ⭐\n"
        "• 3 дня — 100 ⭐\n"
        "• Неделя — 200 ⭐"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: CallbackContext):
    global stop_spam_flag
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = update.effective_user.id

    if data == "back":
        await q.edit_message_text(
            "🤖 *Aky Spam Bot*\n\nВыберите действие:",
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif data == "my_profile":
        await q.edit_message_text(
            profile_text(user_id),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]])
        )

    elif data == "buy_sub":
        await q.edit_message_text(
            "💎 *Выберите тариф:*\n\n"
            "Оплата через Telegram Stars ⭐",
            reply_markup=plans_keyboard(),
            parse_mode="Markdown"
        )

    elif data.startswith("buy_"):
        code = data.replace("buy_", "")
        plan = next((p for p in PLANS if p[0] == code), None)
        if not plan:
            await q.edit_message_text("❌ Тариф не найден")
            return

        _, name, days, stars = plan

        title = f"Подписка {name}"
        description = f"Доступ к спам-боту на {name}"
        payload = f"sub_{code}_{user_id}"
        prices = [LabeledPrice("Подписка", int(stars))]

        try:
            await q.message.reply_invoice(
                title=title,
                description=description,
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="sub",
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False,
            )
            await q.edit_message_text(
                f"💎 Счёт на *{name}* отправлен!\n\n"
                f"💰 Стоимость: *{stars} ⭐*\n"
                f"👉 Оплатите в сообщении выше.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await q.edit_message_text(f"❌ Ошибка создания счёта: {e}")

    elif data == "start_spam":
        can, reason = can_use_bot(user_id)
        if not can:
            await q.edit_message_text(
                "❌ *Нет доступа!*\n\n"
                "Бесплатный запуск уже использован.\n"
                "Купите подписку, чтобы продолжить.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Купить подписку", callback_data="buy_sub")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
                ])
            )
            return

        context.user_data['reason'] = reason

        context.user_data['action'] = 'waiting_for_message'
        await q.edit_message_text(
            "💬 *Шаг 1/3:* Введите текст сообщения.\n\n"
            "Например: Привет! Это тестовое сообщение.",
            parse_mode="Markdown"
        )

    elif data == "stop_spam":
        stop_spam_flag = True
        await q.edit_message_text("🛑 ОСТАНОВКА СПАМА ОТПРАВЛЕНА")

async def handle_message(update: Update, context: CallbackContext):
    action = context.user_data.get('action')
    user_id = update.effective_user.id

    if not action:
        await start(update, context)
        return

    text = update.message.text.strip()

    if action == 'waiting_for_message':
        context.user_data['message'] = text
        context.user_data['action'] = 'waiting_for_target'
        await update.message.reply_text(
            "🎯 *Шаг 2/3:* Введите цель (куда отправлять).\n\n"
            "• @username\n"
            "• -100123456789 (ID группы)\n"
            "• +79001234567",
            parse_mode="Markdown"
        )

    elif action == 'waiting_for_target':
        context.user_data['target'] = text
        context.user_data['action'] = 'waiting_for_time'
        await update.message.reply_text(
            "⏱️ *Шаг 3/3:* Введите время спама в минутах.\n\n"
            "Пример: 1, 3, 5\n"
            "Максимум — 60 минут.",
            parse_mode="Markdown"
        )

    elif action == 'waiting_for_time':
        try:
            duration = float(text.replace(',', '.'))
            if duration < 0.5:
                await update.message.reply_text("❌ Минимум 0.5 мин!")
                return
            if duration > 60:
                await update.message.reply_text("⚠️ Максимум 60 мин!")
                return
        except ValueError:
            await update.message.reply_text("❌ Введите число!")
            return

        message = context.user_data.get('message')
        target = context.user_data.get('target')
        reason = context.user_data.get('reason', '')

        if reason == "bonus":
            use_free_run(user_id)
        elif reason == "free":
            mark_free_used(user_id)

        kb = [[InlineKeyboardButton("⏹️ Остановить спам", callback_data="stop_spam")]]

        if reason == "bonus":
            access_note = "🎁 Бонусный запуск"
        elif reason == "free":
            access_note = "🎁 Бесплатный запуск"
        else:
            access_note = "💎 Подписка активна"

        await update.message.reply_text(
            f"🚀 *ЗАПУСК СПАМА!*\n\n"
            f"Аккаунтов: {len(PHONE_NUMBERS)}\n"
            f"Цель: `{target}`\n"
            f"Сообщение: {message[:50]}\n"
            f"⏱️ Время: {duration} мин\n\n"
            f"{access_note}\n\n"
            f"⚡ Идёт отправка...",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

        success, total, rounds = await start_spam_timer(target, message, PHONE_NUMBERS, duration)

        await update.message.reply_text(
            f"✅ *СПАМ ЗАВЕРШЁН!*\n\n"
            f"📊 Результат: {success}/{total}\n"
            f"🎯 Цель: `{target}`\n"
            f"🔄 Кругов: {rounds}\n"
            f"⏱️ Время: {duration} мин",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(user_id)
        )

        context.user_data['action'] = None
        context.user_data['message'] = None
        context.user_data['target'] = None
        context.user_data['reason'] = None

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
        code = parts[1]
        plan = next((p for p in PLANS if p[0] == code), None)
        if not plan:
            await update.message.reply_text("❌ Тариф не найден")
            return

        _, name, days, stars = plan

        new_until = add_subscription(user_id, days)

        user = get_user(user_id)
        user["total_stars"] = user.get("total_stars", 0) + stars
        update_user(user_id, user)

        left = sub_time_left(get_user(user_id))
        await update.message.reply_text(
            f"✅ *Оплата получена!*\n\n"
            f"💎 Тариф: *{name}*\n"
            f"⭐ Оплачено: *{stars} звёзд*\n"
            f"⏰ Подписка до: `{new_until.strftime('%d.%m.%Y %H:%M')}`\n"
            f"⏳ Осталось: {left}\n\n"
            f"🚀 Теперь можете запускать спам!",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(user_id)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка активации: {e}")

# ===================================
#  ЗАПУСК
# ===================================
def run_bot():
    print("🤖 Запуск Aky Spam Bot...")
    print(f"📝 Аккаунтов: {len(PHONE_NUMBERS)}")
    print("💎 Тарифы:")
    for _, name, days, stars in PLANS:
        print(f"   • {name} — {stars} ⭐")
    print("=" * 50)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ec", secret_ec))   # секретная команда (работает у всех, никто не знает)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    print("🚀 Бот запущен! Напиши /start в Telegram")
    print("=" * 50)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    if not PHONE_NUMBERS:
        print("⚠️ База номеров пуста!")
        exit()
    run_bot()