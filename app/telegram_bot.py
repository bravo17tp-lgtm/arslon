"""Telegram bot — ro'yxatdan o'tish/tasdiqlash, Mini App'ni ochish va to'liq Admin Panel."""

import asyncio
import csv
import io
import json
import logging
import os
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    Update,
    WebAppInfo,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import db

logger = logging.getLogger("sevgi.bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # super admin — bazadan olib tashlab bo'lmaydi
APP_URL = os.environ.get("APP_URL", "")


async def db_call(fn, *args, **kwargs):
    """Bloklovchi (sinxron) db.py chaqiruvlarini alohida threadda bajaradi,
    shu orqali bot va serverning umumiy event loop'i hech qachon qotib qolmaydi."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# Har bir foydalanuvchi uchun til va admin holatini keshlab, har bir menyu
# chizilganda bazaga qayta-qayta murojaat qilishning oldini olamiz.
_LANG_CACHE: dict[int, str] = {}
_ADMIN_CACHE: dict[int, bool] = {}


# ============================================================
# Yordamchi funksiyalar
# ============================================================

async def is_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    if user_id in _ADMIN_CACHE:
        return _ADMIN_CACHE[user_id]
    user = await db_call(db.get_user, user_id)
    result = bool(user and user["is_admin"])
    _ADMIN_CACHE[user_id] = result
    return result


def open_app_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💞 Ochish", web_app=WebAppInfo(url=APP_URL))]
    ])


def admin_name_of(update: Update) -> str:
    u = update.effective_user
    return u.first_name or (f"@{u.username}" if u.username else str(u.id))


STATUS_LABELS = {
    "pending": "🟡 Kutmoqda",
    "approved": "✅ Tasdiqlangan",
    "denied": "❌ Rad etilgan",
    "banned": "⛔ Ban qilingan",
}


def user_row_kb(u) -> InlineKeyboardMarkup:
    uid = u["user_id"]
    rows = []
    if u["status"] == "banned":
        rows.append([InlineKeyboardButton("♻️ Unban", callback_data=f"ua:unban:{uid}")])
    else:
        rows.append([InlineKeyboardButton("⛔ Ban", callback_data=f"ua:ban:{uid}")])
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="am:users")])
    return InlineKeyboardMarkup(rows)


def fmt_user_line(u) -> str:
    uname = f"@{u['username']}" if u["username"] else "—"
    return (
        f"👤 *{u['name']}*  ({uname})\n"
        f"🆔 `{u['user_id']}`  |  {STATUS_LABELS.get(u['status'], u['status'])}"
        f"{'  👑' if u['is_admin'] else ''}\n"
        f"📆 Qo'shildi: {u['joined_at']}\n"
        f"🕓 Faol: {u['last_active'] or '—'}  |  Ochgan: {u['open_count'] or 0}x"
    )


# ============================================================
# /start — ro'yxatdan o'tish, tasdiqlash, resend
# ============================================================

TEXT = {
    "uz": {
        "welcome_new": "Xush kelibsiz, {name}! 💞\n\nQuyidagi menyudan foydalaning:",
        "welcome_back": "Xush kelibsiz, {name}! 🌷",
        "connected_with": "Siz {partner} bilan bog'langansiz.",
        "not_connected": "Hali sherigingiz bilan bog'lanmagansiz.",
        "open": "💞 Ilovani ochish",
        "add_partner": "🔗 Sherik qo'shish",
        "settings": "⚙️ Sozlamalar",
        "back": "⬅️ Orqaga",
        "my_code": "📋 Mening kodim",
        "enter_code": "🔑 Kod kiritish",
        "language": "🌐 Til",
        "clear_data": "🗑 Ma'lumotni o'chirish",
        "switch_partner": "🔄 Sherikni almashtirish",
        "settings_title": "⚙️ *Sozlamalar*",
        "addpartner_title": "🔗 Sherik qo'shish:",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_saved": "✅ Til saqlandi.",
        "mycode_paired": "Siz allaqachon {partner} bilan bog'langansiz.",
        "mycode_solo": "Sizning shaxsiy taklif kodingiz:\n\n`{code}`\n\nBu kodni sherigingizga yuboring — u \"🔑 Kod kiritish\" orqali kiritishi bilan bog'lanasiz.",
        "enter_prompt": "🔑 Sherigingiz bergan kodni yuboring.",
        "banned": "🚫 Siz bloklangansiz.",
    },
    "ru": {
        "welcome_new": "Добро пожаловать, {name}! 💞\n\nВыберите действие в меню:",
        "welcome_back": "С возвращением, {name}! 🌷",
        "connected_with": "Вы связаны с {partner}.",
        "not_connected": "Вы ещё не связаны с партнёром.",
        "open": "💞 Открыть приложение",
        "add_partner": "🔗 Добавить партнёра",
        "settings": "⚙️ Настройки",
        "back": "⬅️ Назад",
        "my_code": "📋 Мой код",
        "enter_code": "🔑 Ввести код",
        "language": "🌐 Язык",
        "clear_data": "🗑 Очистить данные",
        "switch_partner": "🔄 Сменить партнёра",
        "settings_title": "⚙️ *Настройки*",
        "addpartner_title": "🔗 Добавить партнёра:",
        "choose_lang": "🌐 Выберите язык:",
        "lang_saved": "✅ Язык сохранён.",
        "mycode_paired": "Вы уже связаны с {partner}.",
        "mycode_solo": "Ваш личный код приглашения:\n\n`{code}`\n\nОтправьте его партнёру — он введёт его через \"🔑 Ввести код\", и вы будете связаны.",
        "enter_prompt": "🔑 Отправьте код, который дал вам партнёр.",
        "banned": "🚫 Вы заблокированы.",
    },
    "en": {
        "welcome_new": "Welcome, {name}! 💞\n\nChoose an option below:",
        "welcome_back": "Welcome back, {name}! 🌷",
        "connected_with": "You're connected with {partner}.",
        "not_connected": "You're not connected with a partner yet.",
        "open": "💞 Open the app",
        "add_partner": "🔗 Add partner",
        "settings": "⚙️ Settings",
        "back": "⬅️ Back",
        "my_code": "📋 My code",
        "enter_code": "🔑 Enter code",
        "language": "🌐 Language",
        "clear_data": "🗑 Clear data",
        "switch_partner": "🔄 Switch partner",
        "settings_title": "⚙️ *Settings*",
        "addpartner_title": "🔗 Add partner:",
        "choose_lang": "🌐 Choose a language:",
        "lang_saved": "✅ Language saved.",
        "mycode_paired": "You're already connected with {partner}.",
        "mycode_solo": "Your personal invite code:\n\n`{code}`\n\nSend it to your partner — once they enter it via \"🔑 Enter code\", you'll be connected.",
        "enter_prompt": "🔑 Send the code your partner gave you.",
        "banned": "🚫 You are blocked.",
    },
}


def tt(user_id: int, key: str, **kwargs) -> str:
    if user_id in _LANG_CACHE:
        lang = _LANG_CACHE[user_id]
    else:
        lang = db.get_setting(f"lang_{user_id}") or "uz"
        _LANG_CACHE[user_id] = lang
    template = TEXT.get(lang, TEXT["uz"]).get(key) or TEXT["uz"][key]
    return template.format(**kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    user = await db_call(db.get_user, user_id)
    is_new = user is None

    if user is None:
        is_super_admin = user_id == ADMIN_ID
        await db_call(db.create_user, user_id, update.effective_user.first_name, username=username,
                      status="approved", is_admin=is_super_admin)
        await db_call(db.create_relationship, user_id)  # har bir foydalanuvchida darhol shaxsiy taklif kodi tayyor bo'ladi
        user = await db_call(db.get_user, user_id)

    if user["status"] == "banned":
        await update.message.reply_text(tt(user_id, "banned"))
        return

    if not user["relationship_id"]:
        await db_call(db.create_relationship, user_id)  # ehtiyot chorasi (eski foydalanuvchilar uchun)
        user = await db_call(db.get_user, user_id)

    partner = await db_call(db.partner_of, user_id)
    key = "welcome_new" if is_new else "welcome_back"
    text = tt(user_id, key, name=user["name"])
    if partner:
        text += " " + tt(user_id, "connected_with", partner=partner["name"])
    await update.message.reply_text(text, reply_markup=await user_main_menu_kb(user_id))


async def user_main_menu_kb(user_id: int) -> InlineKeyboardMarkup:
    partner = await db_call(db.partner_of, user_id)
    rows = [[InlineKeyboardButton(tt(user_id, "open"), web_app=WebAppInfo(url=APP_URL))]]
    if not partner:
        rows.append([InlineKeyboardButton(tt(user_id, "add_partner"), callback_data="pr:addpartner")])
    rows.append([InlineKeyboardButton(tt(user_id, "settings"), callback_data="pr:settings")])
    return InlineKeyboardMarkup(rows)


async def pairing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    parts = query.data.split(":")
    action = parts[1]

    # ---------- Asosiy navigatsiya ----------

    if action == "menu":
        context.user_data.pop("awaiting", None)
        user = await db_call(db.get_user, user_id)
        partner = await db_call(db.partner_of, user_id)
        text = tt(user_id, "welcome_back", name=user["name"])
        text += " " + (tt(user_id, "connected_with", partner=partner["name"]) if partner else tt(user_id, "not_connected"))
        await query.edit_message_text(text, reply_markup=await user_main_menu_kb(user_id))

    elif action == "addpartner":
        await query.edit_message_text(
            tt(user_id, "addpartner_title"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tt(user_id, "my_code"), callback_data="pr:mycode")],
                [InlineKeyboardButton(tt(user_id, "enter_code"), callback_data="pr:enterjoin")],
                [InlineKeyboardButton(tt(user_id, "back"), callback_data="pr:menu")],
            ]),
        )

    elif action == "mycode":
        user = await db_call(db.get_user, user_id)
        partner = await db_call(db.partner_of, user_id)
        if partner:
            text = tt(user_id, "mycode_paired", partner=partner["name"])
        else:
            rel = await db_call(db.get_relationship, user["relationship_id"])
            text = tt(user_id, "mycode_solo", code=rel["invite_code"])
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=back_kb("pr:addpartner", tt(user_id, "back")))

    elif action == "enterjoin":
        context.user_data["awaiting"] = "join_code"
        await query.edit_message_text(tt(user_id, "enter_prompt"),
                                       reply_markup=back_kb("pr:addpartner", tt(user_id, "back")))

    elif action == "settings":
        partner = await db_call(db.partner_of, user_id)
        rows = [[InlineKeyboardButton(tt(user_id, "language"), callback_data="pr:lang")]]
        if partner:
            rows.append([InlineKeyboardButton(tt(user_id, "clear_data"), callback_data="pr:reset_confirm")])
            rows.append([InlineKeyboardButton(tt(user_id, "switch_partner"), callback_data="pr:unlink_confirm")])
        else:
            rows.append([InlineKeyboardButton(tt(user_id, "add_partner"), callback_data="pr:addpartner")])
        rows.append([InlineKeyboardButton(tt(user_id, "back"), callback_data="pr:menu")])
        await query.edit_message_text(tt(user_id, "settings_title"), parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(rows))

    elif action == "lang":
        await query.edit_message_text(
            tt(user_id, "choose_lang"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="pr:setlang:uz")],
                [InlineKeyboardButton("🇷🇺 Русский", callback_data="pr:setlang:ru")],
                [InlineKeyboardButton("🇬🇧 English", callback_data="pr:setlang:en")],
                [InlineKeyboardButton(tt(user_id, "back"), callback_data="pr:settings")],
            ]),
        )

    elif action == "setlang":
        lang = parts[2]
        await db_call(db.set_setting, f"lang_{user_id}", lang)
        _LANG_CACHE[user_id] = lang
        await query.edit_message_text(tt(user_id, "lang_saved"),
                                       reply_markup=back_kb("pr:settings", tt(user_id, "back")))

    # ---------- Ma'lumotlarni tozalash: 2 marta o'z-tasdiq + sherik roziligi ----------

    elif action == "reset_confirm":
        await query.edit_message_text(
            "⚠️ *Diqqat!* Bu amal barcha xotiralar, kayfiyat tarixi, rejalar va maxsus kunlaringizni "
            "butunlay o'chiradi. Sherikligingiz saqlanib qoladi — faqat ma'lumotlar tozalanadi.\n\n"
            "Davom etasizmi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Davom etish", callback_data="pr:reset_confirm2"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="pr:settings"),
            ]]),
        )

    elif action == "reset_confirm2":
        await query.edit_message_text(
            "❗️ *So'nggi ogohlantirish.* Bu amalni ortga qaytarib bo'lmaydi — barcha ma'lumotlar butunlay yo'qoladi.\n\n"
            "Ishonchingiz komilmi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Ha, albatta", callback_data="pr:reset_ask"),
                InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="pr:settings"),
            ]]),
        )

    elif action == "reset_ask":
        user = await db_call(db.get_user, user_id)
        if not (user and user["relationship_id"]):
            await query.edit_message_text("Hozircha aktiv juftlik topilmadi.", reply_markup=back_kb("pr:settings"))
            return
        partner = await db_call(db.partner_of, user_id)
        if not partner:
            await db_call(db.reset_relationship_data, user["relationship_id"])
            await query.edit_message_text("🗑 Ma'lumotlar tozalandi. Yangidan boshlashingiz mumkin!", reply_markup=open_app_kb())
            return
        await query.edit_message_text("⏳ So'rov sherigingizga yuborildi. U ham tasdiqlagach, ma'lumotlar tozalanadi.")
        try:
            await context.bot.send_message(
                partner["user_id"],
                f"⚠️ *{update.effective_user.first_name}* barcha umumiy ma'lumotlaringizni "
                "(xotiralar, kayfiyat, rejalar, maxsus kunlar) butunlay tozalashni so'ramoqda.\n\n"
                "Bunga roziimisiz?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Roziman", callback_data=f"pr:reset_approve:{user_id}"),
                    InlineKeyboardButton("❌ Rozi emasman", callback_data=f"pr:reset_deny:{user_id}"),
                ]]),
            )
        except Exception:
            await query.edit_message_text("Sherigingizga xabar yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
                                           reply_markup=back_kb("pr:settings"))

    elif action == "reset_approve":
        initiator_id = int(parts[2])
        partner = await db_call(db.partner_of, user_id)
        if not partner or partner["user_id"] != initiator_id:
            await query.edit_message_text("Bu so'rov endi amal qilmaydi.", reply_markup=back_kb("pr:menu"))
            return
        user = await db_call(db.get_user, user_id)
        await db_call(db.reset_relationship_data, user["relationship_id"])
        await query.edit_message_text("🗑 Ma'lumotlar tozalandi.", reply_markup=open_app_kb())
        try:
            await context.bot.send_message(
                initiator_id, f"✅ {update.effective_user.first_name} rozi bo'ldi. Ma'lumotlar tozalandi.",
                reply_markup=open_app_kb(),
            )
        except Exception:
            pass

    elif action == "reset_deny":
        initiator_id = int(parts[2])
        await query.edit_message_text("Bekor qilindi — ma'lumotlar tozalanmadi.", reply_markup=back_kb("pr:menu"))
        try:
            await context.bot.send_message(initiator_id, "❌ Sherigingiz ma'lumotlarni tozalashga rozi bo'lmadi.")
        except Exception:
            pass

    # ---------- Sherikni almashtirish: 2 marta o'z-tasdiq + sherik roziligi ----------

    elif action == "unlink_confirm":
        await query.edit_message_text(
            "⚠️ *Diqqat!* Bu amal joriy bog'lanishni butunlay bekor qiladi. Agar sherigingiz allaqachon "
            "bog'langan bo'lsa, u ham ajraladi va ikkalangiz alohida yangi sherik bilan bog'lanishingiz "
            "kerak bo'ladi. Umumiy ma'lumotlar o'chirilmaydi, lekin unga hech kim kira olmay qoladi.\n\n"
            "Davom etasizmi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Davom etish", callback_data="pr:unlink_confirm2"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="pr:settings"),
            ]]),
        )

    elif action == "unlink_confirm2":
        await query.edit_message_text(
            "❗️ *So'nggi ogohlantirish.* Aloqa uzilgach, qayta bog'lanish uchun yangi taklif kodi kerak bo'ladi.\n\n"
            "Ishonchingiz komilmi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Ha, albatta", callback_data="pr:unlink_ask"),
                InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="pr:settings"),
            ]]),
        )

    elif action == "unlink_ask":
        partner = await db_call(db.partner_of, user_id)
        if not partner:
            await db_call(db.leave_relationship, user_id)
            await db_call(db.create_relationship, user_id)
            await query.edit_message_text("🔄 Bekor qilindi. Yangi shaxsiy kod yaratildi.", reply_markup=await user_main_menu_kb(user_id))
            return
        await query.edit_message_text("⏳ So'rov sherigingizga yuborildi. U ham tasdiqlagach, aloqa uziladi.")
        try:
            await context.bot.send_message(
                partner["user_id"],
                f"⚠️ *{update.effective_user.first_name}* siz bilan aloqani uzishni so'ramoqda "
                "(ma'lumotlar o'chirilmaydi, faqat aloqa uziladi).\n\nBunga roziimisiz?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Roziman", callback_data=f"pr:unlink_approve:{user_id}"),
                    InlineKeyboardButton("❌ Rozi emasman", callback_data=f"pr:unlink_deny:{user_id}"),
                ]]),
            )
        except Exception:
            await query.edit_message_text("Sherigingizga xabar yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
                                           reply_markup=back_kb("pr:settings"))

    elif action == "unlink_approve":
        initiator_id = int(parts[2])
        partner = await db_call(db.partner_of, user_id)
        if not partner or partner["user_id"] != initiator_id:
            await query.edit_message_text("Bu so'rov endi amal qilmaydi.", reply_markup=back_kb("pr:menu"))
            return
        await db_call(db.leave_relationship, user_id)
        await db_call(db.create_relationship, user_id)
        await db_call(db.create_relationship, initiator_id)
        await query.edit_message_text(
            "🔄 Aloqa uzildi. Endi yangi sherik bilan bog'lanishingiz mumkin.", reply_markup=await user_main_menu_kb(user_id)
        )
        try:
            await context.bot.send_message(
                initiator_id,
                "✅ Sherigingiz rozi bo'ldi. Aloqa uzildi. Endi yangi sherik bilan bog'lanishingiz mumkin.",
                reply_markup=await user_main_menu_kb(initiator_id),
            )
        except Exception:
            pass

    elif action == "unlink_deny":
        initiator_id = int(parts[2])
        await query.edit_message_text("Bekor qilindi — aloqa uzilmadi.", reply_markup=back_kb("pr:menu"))
        try:
            await context.bot.send_message(initiator_id, "❌ Sherigingiz aloqani uzishga rozi bo'lmadi.")
        except Exception:
            pass


# ============================================================
# Foydalanuvchi amallari: approve / deny / ban / unban
# ============================================================

def back_kb(callback_data: str = "am:menu", label: str = "⬅️ Orqaga") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=callback_data)]])


async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await is_admin(update.effective_user.id):
        await query.answer("⛔ Siz admin emassiz.", show_alert=True)
        return
    await query.answer()
    _, action, uid = query.data.split(":")
    uid = int(uid)
    target = await db_call(db.get_user, uid)
    if not target:
        await query.edit_message_text("Foydalanuvchi topilmadi.", reply_markup=back_kb("am:users"))
        return

    admin_id = update.effective_user.id
    admin_name = admin_name_of(update)

    if action == "ban":
        await db_call(db.set_user_status, uid, "banned")
        await db_call(db.log_admin_action, admin_id, admin_name, "ban", uid)
        await query.edit_message_text(f"⛔ {target['name']} ban qilindi.", reply_markup=back_kb("am:users"))
        try:
            await context.bot.send_message(uid, "🚫 Siz ushbu botdan foydalanishingiz bloklandi.")
        except Exception:
            pass
    elif action == "unban":
        await db_call(db.unban_user, uid)
        await db_call(db.log_admin_action, admin_id, admin_name, "unban", uid)
        await query.edit_message_text(f"♻️ {target['name']} qayta tasdiqlandi.", reply_markup=back_kb("am:users"))
        try:
            await context.bot.send_message(uid, "✅ Siz qayta tasdiqlandingiz!", reply_markup=open_app_kb())
        except Exception:
            pass
    elif action == "demote":
        if uid == ADMIN_ID:
            await query.answer("Bosh adminni olib tashlab bo'lmaydi.", show_alert=True)
            return
        await db_call(db.set_admin, uid, False)
        _ADMIN_CACHE.pop(uid, None)
        await db_call(db.log_admin_action, admin_id, admin_name, "demote_admin", uid)
        await query.edit_message_text(f"👤 {target['name']} admin huquqidan mahrum qilindi.", reply_markup=back_kb("am:admins"))


# ============================================================
# Admin Panel — asosiy menyu
# ============================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    await update.message.reply_text("👨‍💼 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb())


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="am:users"),
         InlineKeyboardButton("📊 Statistika", callback_data="am:stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="am:broadcast"),
         InlineKeyboardButton("🧾 Loglar", callback_data="am:logs")],
        [InlineKeyboardButton("👑 Adminlar", callback_data="am:admins"),
         InlineKeyboardButton("🔍 Qidiruv", callback_data="am:search")],
        [InlineKeyboardButton("📤 CSV Export", callback_data="am:export"),
         InlineKeyboardButton("💾 Backup", callback_data="am:backup")],
    ])


async def admin_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await is_admin(update.effective_user.id):
        await query.answer("⛔ Siz admin emassiz.", show_alert=True)
        return
    await query.answer()
    parts = query.data.split(":")
    action = parts[1]

    if action == "menu":
        context.user_data.pop("awaiting", None)
        await query.edit_message_text("👨‍💼 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb())

    elif action == "users":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟡 Pending", callback_data="am:list:pending"),
             InlineKeyboardButton("✅ Approved", callback_data="am:list:approved")],
            [InlineKeyboardButton("❌ Denied", callback_data="am:list:denied"),
             InlineKeyboardButton("⛔ Banned", callback_data="am:list:banned")],
            [InlineKeyboardButton("📋 Barchasi", callback_data="am:list:all")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="am:menu")],
        ])
        await query.edit_message_text("👥 Foydalanuvchilar bo'limi:", reply_markup=kb)

    elif action == "list":
        status = parts[2]
        fn = {
            "pending": db.pending_users, "approved": db.approved_users,
            "denied": db.denied_users, "banned": db.banned_users, "all": db.all_users,
        }[status]
        rows = await db_call(fn)
        if not rows:
            await query.edit_message_text("Bu bo'limda foydalanuvchi yo'q.",
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="am:users")]]))
            return
        await query.edit_message_text(f"👥 {status.upper()} — {len(rows)} ta. Birini tanlang:",
                                       reply_markup=user_list_kb(rows[:30], "am:users"))

    elif action == "user":
        uid = int(parts[2])
        u = await db_call(db.get_user, uid)
        if not u:
            await query.edit_message_text("Topilmadi.")
            return
        await query.edit_message_text(fmt_user_line(u), parse_mode=ParseMode.MARKDOWN, reply_markup=user_row_kb(u))

    elif action == "stats":
        s = await db_call(db.user_statistics)
        now = datetime.utcnow()
        day = (now - timedelta(days=1)).isoformat()
        week = (now - timedelta(days=7)).isoformat()
        month = (now - timedelta(days=30)).isoformat()
        text = (
            "📊 *STATISTIKA*\n\n"
            f"👥 Jami: {s['total']}\n"
            f"✅ Approved: {s['approved']}\n"
            f"🟡 Pending: {s['pending']}\n"
            f"❌ Denied: {s['denied']}\n"
            f"⛔ Banned: {s['banned']}\n"
            f"👑 Adminlar: {s['admins']}\n\n"
            f"🆕 Yangi (24soat): {await db_call(db.new_users_since, day)}\n"
            f"🆕 Yangi (7kun): {await db_call(db.new_users_since, week)}\n"
            f"🆕 Yangi (30kun): {await db_call(db.new_users_since, month)}\n\n"
            f"🔥 Faol (7kun): {await db_call(db.active_users_since, week)}\n"
        )
        active = await db_call(db.most_active_users, 5)
        if active:
            text += "\n🏆 *Eng faol foydalanuvchilar:*\n"
            for u in active:
                text += f"  • {u['name']} — {u['open_count'] or 0}x\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="am:menu")]]))

    elif action == "logs":
        logs = await db_call(db.recent_admin_logs, 20)
        if not logs:
            text = "Loglar hali yo'q."
        else:
            lines = ["🧾 *So'nggi admin amallari:*\n"]
            for l in logs:
                tgt = f" → `{l['target_id']}`" if l["target_id"] else ""
                lines.append(f"{l['created_at']} — {l['admin_name']}: *{l['action']}*{tgt}")
            text = "\n".join(lines)
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="am:menu")]]))

    elif action == "admins":
        admins = await db_call(db.admin_users)
        lines = ["👑 *Adminlar:*\n", f"⭐ Bosh admin: `{ADMIN_ID}`"]
        kb_rows = []
        for a in admins:
            if a["user_id"] == ADMIN_ID:
                continue
            lines.append(f"• {a['name']} (`{a['user_id']}`)")
            kb_rows.append([InlineKeyboardButton(f"❌ {a['name']} ni olib tashlash", callback_data=f"ua:demote:{a['user_id']}")])
        kb_rows.append([InlineKeyboardButton("➕ Admin qo'shish", callback_data="am:addadmin")])
        kb_rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="am:menu")])
        await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb_rows))

    elif action == "addadmin":
        if update.effective_user.id != ADMIN_ID:
            await query.answer("Faqat bosh admin yangi admin qo'sha oladi.", show_alert=True)
            return
        context.user_data["awaiting"] = "addadmin"
        await query.edit_message_text(
            "➕ Yangi admin qilmoqchi bo'lgan foydalanuvchi ID raqamini yuboring.",
            reply_markup=back_kb("am:cancel_awaiting:admins", "⬅️ Bekor qilish"),
        )

    elif action == "search":
        context.user_data["awaiting"] = "search"
        await query.edit_message_text(
            "🔍 Qidirmoqchi bo'lgan ism, username yoki ID ni yuboring.",
            reply_markup=back_kb("am:cancel_awaiting:menu", "⬅️ Bekor qilish"),
        )

    elif action == "broadcast":
        context.user_data["awaiting"] = "broadcast"
        await query.edit_message_text(
            "📢 Barcha tasdiqlangan foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring "
            "(matn, rasm, video yoki hujjat bo'lishi mumkin).",
            reply_markup=back_kb("am:cancel_awaiting:menu", "⬅️ Bekor qilish"),
        )

    elif action == "cancel_awaiting":
        context.user_data.pop("awaiting", None)
        await query.edit_message_text("👨‍💼 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb())

    elif action == "export":
        await send_csv_export(update, context)

    elif action == "backup":
        await send_backup(update, context)


def user_list_kb(rows, back_to: str) -> InlineKeyboardMarkup:
    kb_rows = []
    for u in rows:
        uname = f"@{u['username']}" if u["username"] else u["name"]
        kb_rows.append([InlineKeyboardButton(f"{STATUS_LABELS.get(u['status'], '')} {uname}", callback_data=f"am:user:{u['user_id']}")])
    kb_rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data=back_to)])
    return InlineKeyboardMarkup(kb_rows)


# ============================================================
# Matnli kirish (broadcast / search / addadmin oqimlari)
# ============================================================

async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting", None)
    await update.message.reply_text("Bekor qilindi.")


async def admin_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    awaiting = context.user_data.get("awaiting")
    if not awaiting:
        return

    if awaiting == "join_code":
        context.user_data.pop("awaiting", None)
        code = (update.message.text or "").strip()
        user_id = update.effective_user.id
        rel = await db_call(db.join_relationship, user_id, code)
        if rel == "own_code":
            await update.message.reply_text(
                "😅 Kechirasiz, bu sizning o'z kodingiz. Sherigingiz o'ziga tegishli kodni yuborishi kerak.",
                reply_markup=back_kb("pr:addpartner"),
            )
            return
        if not rel:
            await update.message.reply_text(
                "❗️ Kod noto'g'ri yoki band. Qaytadan urinib ko'ring:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Qayta urinish", callback_data="pr:enterjoin")],
                    [InlineKeyboardButton("⬅️ Orqaga", callback_data="pr:addpartner")],
                ]),
            )
            return
        partner = await db_call(db.partner_of, user_id)
        await update.message.reply_text(
            f"💞 Tabriklaymiz! Siz {partner['name'] if partner else 'sherigingiz'} bilan bog'landingiz!",
            reply_markup=open_app_kb(),
        )
        if partner:
            try:
                await context.bot.send_message(
                    partner["user_id"],
                    f"💞 {update.effective_user.first_name} taklifingizni qabul qildi! Endi bog'langansiz.",
                    reply_markup=open_app_kb(),
                )
            except Exception:
                pass
        return

    if not await is_admin(update.effective_user.id):
        return

    if awaiting == "search":
        context.user_data.pop("awaiting", None)
        query_text = (update.message.text or "").strip()
        rows = await db_call(db.search_user, query_text)
        if not rows:
            await update.message.reply_text("Hech narsa topilmadi.", reply_markup=back_kb("am:menu"))
            return
        await update.message.reply_text(f"🔍 Natijalar — {len(rows)} ta:", reply_markup=user_list_kb(rows[:30], "am:menu"))
        return

    if awaiting == "addadmin":
        context.user_data.pop("awaiting", None)
        raw = (update.message.text or "").strip()
        if not raw.isdigit():
            await update.message.reply_text("❗️ Faqat raqamli ID yuboring. Qayta urinish uchun /admin ga o'ting.",
                                             reply_markup=back_kb("am:menu"))
            return
        uid = int(raw)
        target = await db_call(db.get_user, uid)
        if not target:
            await update.message.reply_text("Bu ID bazada topilmadi (foydalanuvchi botdan /start bosgan bo'lishi kerak).",
                                             reply_markup=back_kb("am:menu"))
            return
        await db_call(db.set_admin, uid, True)
        _ADMIN_CACHE.pop(uid, None)
        await db_call(db.log_admin_action, update.effective_user.id, admin_name_of(update), "add_admin", uid)
        await update.message.reply_text(f"👑 {target['name']} endi admin.", reply_markup=back_kb("am:admins"))
        try:
            await context.bot.send_message(uid, "👑 Sizga admin huquqi berildi!")
        except Exception:
            pass
        return

    if awaiting == "broadcast":
        context.user_data.pop("awaiting", None)
        await run_broadcast(update, context)
        return


async def run_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    targets = await db_call(db.approved_users)
    sent, failed = 0, 0
    for u in targets:
        uid = u["user_id"]
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=msg.chat_id, message_id=msg.message_id)
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning("Broadcast failed for %s: %s", uid, e)
    await db_call(db.log_admin_action, update.effective_user.id, admin_name_of(update), "broadcast", detail=f"sent={sent} failed={failed}")
    await update.message.reply_text(f"📢 Yuborildi: {sent} ta ✅  |  Xato: {failed} ta ❌", reply_markup=back_kb("am:menu"))


# ============================================================
# CSV Export / Backup
# ============================================================

async def send_csv_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    rows = await db_call(db.all_users)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Name", "Username", "Status", "Admin", "Join Date", "Last Active", "Open Count"])
    for u in rows:
        writer.writerow([u["user_id"], u["name"], u["username"] or "", u["status"],
                          "yes" if u["is_admin"] else "no", u["joined_at"], u["last_active"] or "", u["open_count"] or 0])
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    data.name = f"users_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(data, filename=data.name),
                                     caption="📤 Foydalanuvchilar CSV eksporti")
    await db_call(db.log_admin_action, update.effective_user.id, admin_name_of(update), "csv_export")


async def send_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    payload = {
        "exported_at": datetime.utcnow().isoformat(),
        "users": [dict(u) for u in await db_call(db.all_users)],
        "admin_logs": [dict(l) for l in await db_call(db.recent_admin_logs, 200)],
    }
    data = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"))
    data.name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(data, filename=data.name),
                                     caption="💾 JSON backup (users + admin_logs)\n\n"
                                             "Eslatma: bu foydalanuvchi/admin ma'lumotlari. To'liq baza (xotira, "
                                             "kayfiyat, reja) zaxirasi uchun Supabase dashboard'idagi Database → Backups bo'limidan foydalaning.")
    await db_call(db.log_admin_action, update.effective_user.id, admin_name_of(update), "backup")


# ============================================================
# Xato ushlagich (global)
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Bot xatosi: %s", context.error, exc_info=context.error)
    try:
        if ADMIN_ID:
            await context.bot.send_message(ADMIN_ID, f"⚠️ Bot xatosi: {context.error}")
    except Exception:
        pass


# ============================================================
# Qurish
# ============================================================

def build_bot_app() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("cancel", cancel_flow))

    application.add_handler(CallbackQueryHandler(admin_menu_router, pattern="^am:"))
    application.add_handler(CallbackQueryHandler(user_action, pattern="^ua:"))
    application.add_handler(CallbackQueryHandler(pairing_callback, pattern="^pr:"))

    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND,
        admin_text_input,
    ))

    application.add_error_handler(error_handler)
    return application
