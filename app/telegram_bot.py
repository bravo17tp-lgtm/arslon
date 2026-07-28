"""Telegram bot — ro'yxatdan o'tish/tasdiqlash, Mini App'ni ochish va to'liq Admin Panel."""

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
from . import i18n
from .i18n import t

logger = logging.getLogger("sevgi.bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # super admin — bazadan olib tashlab bo'lmaydi
APP_URL = os.environ.get("APP_URL", "")


# ============================================================
# Yordamchi funksiyalar
# ============================================================

def is_admin(user_id: int, user=None) -> bool:
    if user_id == ADMIN_ID:
        return True
    if user is None:
        user = db.get_user(user_id)
    return bool(user and user["is_admin"])


def get_lang(user) -> str:
    if not user:
        return i18n.DEFAULT_LANG
    try:
        lang = user["ui_lang"]
    except (KeyError, IndexError, TypeError):
        lang = None
    return lang if lang in i18n.LANGS else i18n.DEFAULT_LANG


def open_app_kb(lang: str = i18n.DEFAULT_LANG) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_open", lang), web_app=WebAppInfo(url=APP_URL))]
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
# Menyu klaviaturalari
# ============================================================

def new_user_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Sherik hali ulanmagan foydalanuvchi uchun asosiy menyu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_open", lang), web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton(t("btn_add_partner", lang), callback_data="nav:addpartner")],
        [InlineKeyboardButton(t("btn_settings", lang), callback_data="nav:settings")],
    ])


def minimal_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Sherik ulangan (yoki kutayotgan) foydalanuvchi uchun minimal asosiy menyu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_open", lang), web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton(t("btn_settings", lang), callback_data="nav:settings")],
    ])


def addpartner_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_get_code", lang), callback_data="ap:get_code")],
        [InlineKeyboardButton(t("btn_enter_code", lang), callback_data="ap:enter_code")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="nav:main")],
    ])


def settings_kb(user, lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(t("btn_language", lang), callback_data="nav:language")]]
    if user and user["relationship_id"]:
        partner = db.partner_of(user["user_id"])
        if partner:
            rows.append([InlineKeyboardButton(t("btn_reset_data", lang), callback_data="st:reset_confirm")])
            rows.append([InlineKeyboardButton(t("btn_change_partner", lang), callback_data="st:unlink_confirm")])
        else:
            rows.append([InlineKeyboardButton(t("btn_cancel_invite", lang), callback_data="st:unlink_confirm")])
    else:
        rows.append([InlineKeyboardButton(t("btn_connect_partner", lang), callback_data="nav:addpartner")])
    if user and is_admin(user["user_id"], user):
        rows.append([InlineKeyboardButton(t("btn_admin_panel", lang), callback_data="nav:adminpanel")])
    rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="nav:main")])
    return InlineKeyboardMarkup(rows)


def language_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for code in i18n.LANGS:
        label = i18n.LANG_NAMES[code] + (" ✅" if code == lang else "")
        rows.append([InlineKeyboardButton(label, callback_data=f"lang:set:{code}")])
    rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="nav:settings")])
    return InlineKeyboardMarkup(rows)


# ============================================================
# /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    user = db.get_user(user_id)

    if user is None:
        is_super_admin = user_id == ADMIN_ID
        db.create_user(user_id, update.effective_user.first_name, username=username,
                        status="approved", is_admin=is_super_admin)
        user = db.get_user(user_id)

    lang = get_lang(user)

    if user["status"] == "banned":
        await update.message.reply_text(t("banned", lang))
        return

    context.user_data.pop("awaiting", None)
    await render_main_menu(update, context, edit=False, user=user)


async def render_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False, user=None):
    """Asosiy menyuni holatga qarab chiqaradi: yangi / sherik kutmoqda / bog'langan."""
    user_id = update.effective_user.id
    if user is None:
        user = db.get_user(user_id)
    lang = get_lang(user)

    if user["relationship_id"]:
        partner = db.partner_of(user_id)
        if partner:
            text = t("welcome_paired", lang, name=user["name"], partner=partner["name"])
            parse_mode = None
        else:
            rel = db.get_relationship(user["relationship_id"])
            text = t("welcome_waiting", lang, code=rel["invite_code"])
            parse_mode = ParseMode.MARKDOWN
        kb = minimal_menu_kb(lang)
    else:
        text = t("welcome_new", lang, name=user["name"])
        parse_mode = None
        kb = new_user_menu_kb(lang)

    if edit:
        await update.callback_query.edit_message_text(text, parse_mode=parse_mode, reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=kb)


# ============================================================
# Navigatsiya (asosiy / sherik qo'shish / sozlamalar / til / admin)
# ============================================================

async def nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    lang = get_lang(user)
    target = query.data.split(":", 1)[1]

    if target == "main":
        context.user_data.pop("awaiting", None)
        await render_main_menu(update, context, edit=True, user=user)

    elif target == "addpartner":
        context.user_data.pop("awaiting", None)
        await query.edit_message_text(
            t("addpartner_title", lang), parse_mode=ParseMode.MARKDOWN, reply_markup=addpartner_kb(lang)
        )

    elif target == "settings":
        context.user_data.pop("awaiting", None)
        await query.edit_message_text(
            t("settings_title", lang), parse_mode=ParseMode.MARKDOWN, reply_markup=settings_kb(user, lang)
        )

    elif target == "language":
        await query.edit_message_text(t("language_title", lang), reply_markup=language_kb(lang))

    elif target == "adminpanel":
        if not is_admin(user_id):
            await query.answer(t("not_admin", lang), show_alert=True)
            return
        context.user_data.pop("awaiting", None)
        await query.edit_message_text("👨‍💼 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb())


async def lang_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    lang = query.data.split(":")[2]
    if lang not in i18n.LANGS:
        lang = i18n.DEFAULT_LANG
    db.set_user_lang(user_id, lang)
    await query.answer(t("language_set", lang))
    user = db.get_user(user_id)
    await query.edit_message_text(
        t("settings_title", lang), parse_mode=ParseMode.MARKDOWN, reply_markup=settings_kb(user, lang)
    )


# ============================================================
# Sherik qo'shish (taklif kodi olish / kiritish)
# ============================================================

async def addpartner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    lang = get_lang(user)
    action = query.data.split(":", 1)[1]

    if action == "get_code":
        if user["relationship_id"]:
            rel = db.get_relationship(user["relationship_id"])
        else:
            rel = db.create_relationship(user_id)
        await query.edit_message_text(
            t("own_code_shown", lang, code=rel["invite_code"], enter_btn=t("btn_enter_code", lang)),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back", lang), callback_data="nav:addpartner")]]),
        )

    elif action == "enter_code":
        context.user_data["awaiting"] = "join_code"
        await query.edit_message_text(
            t("ask_enter_code", lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", lang), callback_data="ap:cancel")]]),
        )

    elif action == "cancel":
        context.user_data.pop("awaiting", None)
        await query.edit_message_text(
            t("addpartner_title", lang), parse_mode=ParseMode.MARKDOWN, reply_markup=addpartner_kb(lang)
        )


# ============================================================
# Sozlamalar ichidagi amallar: ma'lumotni o'chirish / sherikni almashtirish
# (2 marta o'z-tasdiq + sherik roziligi)
# ============================================================

async def settings_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    lang = get_lang(user)
    parts = query.data.split(":")
    action = parts[1]

    if action == "cancel":
        await query.edit_message_text(
            t("settings_title", lang), parse_mode=ParseMode.MARKDOWN, reply_markup=settings_kb(user, lang)
        )
        return

    # ---------- Ma'lumotlarni tozalash ----------

    if action == "reset_confirm":
        await query.edit_message_text(
            t("reset_confirm1", lang), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_continue", lang), callback_data="st:reset_confirm2"),
                InlineKeyboardButton(t("btn_cancel", lang), callback_data="st:cancel"),
            ]]),
        )

    elif action == "reset_confirm2":
        await query.edit_message_text(
            t("reset_confirm2", lang), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_yes_sure", lang), callback_data="st:reset_ask"),
                InlineKeyboardButton(t("btn_no_cancel", lang), callback_data="st:cancel"),
            ]]),
        )

    elif action == "reset_ask":
        if not (user and user["relationship_id"]):
            await query.edit_message_text(t("reset_no_relationship", lang))
            return
        partner = db.partner_of(user_id)
        if not partner:
            db.reset_relationship_data(user["relationship_id"])
            await query.edit_message_text(t("reset_done_alone", lang), reply_markup=open_app_kb(lang))
            return
        await query.edit_message_text(t("reset_sent_to_partner", lang))
        partner_lang = get_lang(partner)
        try:
            await context.bot.send_message(
                partner["user_id"],
                t("reset_ask_partner", partner_lang, name=update.effective_user.first_name),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(t("btn_agree", partner_lang), callback_data=f"st:reset_approve:{user_id}"),
                    InlineKeyboardButton(t("btn_disagree", partner_lang), callback_data=f"st:reset_deny:{user_id}"),
                ]]),
            )
        except Exception:
            await query.edit_message_text(t("reset_send_fail", lang))

    elif action == "reset_approve":
        initiator_id = int(parts[2])
        partner = db.partner_of(user_id)
        if not partner or partner["user_id"] != initiator_id:
            await query.edit_message_text(t("reset_expired", lang))
            return
        db.reset_relationship_data(user["relationship_id"])
        await query.edit_message_text(t("reset_done", lang), reply_markup=open_app_kb(lang))
        initiator_lang = get_lang(db.get_user(initiator_id))
        try:
            await context.bot.send_message(
                initiator_id, t("reset_approved_notice", initiator_lang, name=update.effective_user.first_name),
                reply_markup=open_app_kb(initiator_lang),
            )
        except Exception:
            pass

    elif action == "reset_deny":
        initiator_id = int(parts[2])
        await query.edit_message_text(t("reset_cancelled", lang))
        initiator_lang = get_lang(db.get_user(initiator_id))
        try:
            await context.bot.send_message(initiator_id, t("reset_denied_notice", initiator_lang))
        except Exception:
            pass

    # ---------- Sherikni almashtirish / taklifni bekor qilish ----------

    elif action == "unlink_confirm":
        await query.edit_message_text(
            t("unlink_confirm1", lang), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_continue", lang), callback_data="st:unlink_confirm2"),
                InlineKeyboardButton(t("btn_cancel", lang), callback_data="st:cancel"),
            ]]),
        )

    elif action == "unlink_confirm2":
        await query.edit_message_text(
            t("unlink_confirm2", lang), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_yes_sure", lang), callback_data="st:unlink_ask"),
                InlineKeyboardButton(t("btn_no_cancel", lang), callback_data="st:cancel"),
            ]]),
        )

    elif action == "unlink_ask":
        partner = db.partner_of(user_id)
        if not partner:
            db.leave_relationship(user_id)
            await query.edit_message_text(t("unlink_done_alone", lang), reply_markup=new_user_menu_kb(lang))
            return
        await query.edit_message_text(t("unlink_sent_to_partner", lang))
        partner_lang = get_lang(partner)
        try:
            await context.bot.send_message(
                partner["user_id"],
                t("unlink_ask_partner", partner_lang, name=update.effective_user.first_name),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(t("btn_agree", partner_lang), callback_data=f"st:unlink_approve:{user_id}"),
                    InlineKeyboardButton(t("btn_disagree", partner_lang), callback_data=f"st:unlink_deny:{user_id}"),
                ]]),
            )
        except Exception:
            await query.edit_message_text(t("reset_send_fail", lang))

    elif action == "unlink_approve":
        initiator_id = int(parts[2])
        partner = db.partner_of(user_id)
        if not partner or partner["user_id"] != initiator_id:
            await query.edit_message_text(t("reset_expired", lang))
            return
        db.leave_relationship(user_id)
        await query.edit_message_text(t("unlink_done", lang), reply_markup=new_user_menu_kb(lang))
        initiator_lang = get_lang(db.get_user(initiator_id))
        try:
            await context.bot.send_message(
                initiator_id, t("unlink_approved_notice", initiator_lang),
                reply_markup=new_user_menu_kb(initiator_lang),
            )
        except Exception:
            pass

    elif action == "unlink_deny":
        initiator_id = int(parts[2])
        await query.edit_message_text(t("unlink_cancelled", lang))
        initiator_lang = get_lang(db.get_user(initiator_id))
        try:
            await context.bot.send_message(initiator_id, t("unlink_denied_notice", initiator_lang))
        except Exception:
            pass


# ============================================================
# Foydalanuvchi amallari: approve / deny / ban / unban
# ============================================================

def back_kb(callback_data: str = "am:menu", label: str = "⬅️ Orqaga") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=callback_data)]])


async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(update.effective_user.id):
        await query.answer(t("not_admin", get_lang(db.get_user(update.effective_user.id))), show_alert=True)
        return
    await query.answer()
    _, action, uid = query.data.split(":")
    uid = int(uid)
    target = db.get_user(uid)
    if not target:
        await query.edit_message_text("Foydalanuvchi topilmadi.", reply_markup=back_kb("am:users"))
        return

    admin_id = update.effective_user.id
    admin_name = admin_name_of(update)

    if action == "ban":
        db.set_user_status(uid, "banned")
        db.log_admin_action(admin_id, admin_name, "ban", uid)
        await query.edit_message_text(f"⛔ {target['name']} ban qilindi.", reply_markup=back_kb("am:users"))
        try:
            await context.bot.send_message(uid, t("banned", get_lang(target)))
        except Exception:
            pass
    elif action == "unban":
        db.unban_user(uid)
        db.log_admin_action(admin_id, admin_name, "unban", uid)
        await query.edit_message_text(f"♻️ {target['name']} qayta tasdiqlandi.", reply_markup=back_kb("am:users"))
        try:
            target_lang = get_lang(target)
            await context.bot.send_message(uid, "✅ Siz qayta tasdiqlandingiz!", reply_markup=open_app_kb(target_lang))
        except Exception:
            pass
    elif action == "demote":
        if uid == ADMIN_ID:
            await query.answer("Bosh adminni olib tashlab bo'lmaydi.", show_alert=True)
            return
        db.set_admin(uid, False)
        db.log_admin_action(admin_id, admin_name, "demote_admin", uid)
        await query.edit_message_text(f"👤 {target['name']} admin huquqidan mahrum qilindi.", reply_markup=back_kb("am:admins"))


# ============================================================
# Admin Panel — asosiy menyu
# ============================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", get_lang(db.get_user(update.effective_user.id))))
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
        [InlineKeyboardButton("⬅️ Bot menyusiga qaytish", callback_data="nav:settings")],
    ])


async def admin_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(update.effective_user.id):
        await query.answer(t("not_admin", get_lang(db.get_user(update.effective_user.id))), show_alert=True)
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
        rows = {
            "pending": db.pending_users, "approved": db.approved_users,
            "denied": db.denied_users, "banned": db.banned_users, "all": db.all_users,
        }[status]()
        if not rows:
            await query.edit_message_text("Bu bo'limda foydalanuvchi yo'q.",
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="am:users")]]))
            return
        await query.edit_message_text(f"👥 {status.upper()} — {len(rows)} ta. Birini tanlang:",
                                       reply_markup=user_list_kb(rows[:30], "am:users"))

    elif action == "user":
        uid = int(parts[2])
        u = db.get_user(uid)
        if not u:
            await query.edit_message_text("Topilmadi.")
            return
        await query.edit_message_text(fmt_user_line(u), parse_mode=ParseMode.MARKDOWN, reply_markup=user_row_kb(u))

    elif action == "stats":
        s = db.user_statistics()
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
            f"🆕 Yangi (24soat): {db.new_users_since(day)}\n"
            f"🆕 Yangi (7kun): {db.new_users_since(week)}\n"
            f"🆕 Yangi (30kun): {db.new_users_since(month)}\n\n"
            f"🔥 Faol (7kun): {db.active_users_since(week)}\n"
        )
        active = db.most_active_users(5)
        if active:
            text += "\n🏆 *Eng faol foydalanuvchilar:*\n"
            for u in active:
                text += f"  • {u['name']} — {u['open_count'] or 0}x\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="am:menu")]]))

    elif action == "logs":
        logs = db.recent_admin_logs(20)
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
        admins = db.admin_users()
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
# Matnli kirish (join_code / broadcast / search / addadmin oqimlari)
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
        lang = get_lang(db.get_user(user_id))
        rel = db.join_relationship(user_id, code)
        if rel == "own_code":
            await update.message.reply_text(
                t("own_code_error", lang),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t("btn_retry", lang), callback_data="ap:enter_code")],
                    [InlineKeyboardButton(t("btn_back", lang), callback_data="ap:cancel")],
                ]),
            )
            return
        if not rel:
            await update.message.reply_text(
                t("code_invalid", lang),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t("btn_retry", lang), callback_data="ap:enter_code")],
                    [InlineKeyboardButton(t("btn_back", lang), callback_data="ap:cancel")],
                ]),
            )
            return
        partner = db.partner_of(user_id)
        partner_name = partner["name"] if partner else t("partner_fallback", lang)
        await update.message.reply_text(
            t("joined_success", lang, partner=partner_name),
            reply_markup=open_app_kb(lang),
        )
        if partner:
            partner_lang = get_lang(partner)
            try:
                await context.bot.send_message(
                    partner["user_id"],
                    t("partner_joined_notice", partner_lang, name=update.effective_user.first_name),
                    reply_markup=open_app_kb(partner_lang),
                )
            except Exception:
                pass
        return

    if not is_admin(update.effective_user.id):
        return

    if awaiting == "search":
        context.user_data.pop("awaiting", None)
        query_text = (update.message.text or "").strip()
        rows = db.search_user(query_text)
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
        target = db.get_user(uid)
        if not target:
            await update.message.reply_text("Bu ID bazada topilmadi (foydalanuvchi botdan /start bosgan bo'lishi kerak).",
                                             reply_markup=back_kb("am:menu"))
            return
        db.set_admin(uid, True)
        db.log_admin_action(update.effective_user.id, admin_name_of(update), "add_admin", uid)
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
    targets = db.approved_users()
    sent, failed = 0, 0
    for u in targets:
        uid = u["user_id"]
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=msg.chat_id, message_id=msg.message_id)
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning("Broadcast failed for %s: %s", uid, e)
    db.log_admin_action(update.effective_user.id, admin_name_of(update), "broadcast", detail=f"sent={sent} failed={failed}")
    await update.message.reply_text(f"📢 Yuborildi: {sent} ta ✅  |  Xato: {failed} ta ❌", reply_markup=back_kb("am:menu"))


# ============================================================
# CSV Export / Backup
# ============================================================

async def send_csv_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    rows = db.all_users()
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
    db.log_admin_action(update.effective_user.id, admin_name_of(update), "csv_export")


async def send_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # 1) to'liq SQLite fayl
    try:
        with open(db.DB_PATH, "rb") as f:
            await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(f, filename="love_backup.db"),
                                             caption="💾 To'liq SQLite backup")
    except Exception as e:
        await context.bot.send_message(query.message.chat_id, f"DB faylini yuborishda xato: {e}")

    # 2) o'qish uchun qulay JSON (users + adminlar)
    payload = {
        "exported_at": datetime.utcnow().isoformat(),
        "users": [dict(u) for u in db.all_users()],
        "admin_logs": [dict(l) for l in db.recent_admin_logs(200)],
    }
    data = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    data.name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(data, filename=data.name),
                                     caption="💾 JSON backup (users + admin_logs)")
    db.log_admin_action(update.effective_user.id, admin_name_of(update), "backup")


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
    application.add_handler(CallbackQueryHandler(nav_callback, pattern="^nav:"))
    application.add_handler(CallbackQueryHandler(addpartner_callback, pattern="^ap:"))
    application.add_handler(CallbackQueryHandler(settings_action_callback, pattern="^st:"))
    application.add_handler(CallbackQueryHandler(lang_set_callback, pattern="^lang:set:"))

    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND,
        admin_text_input,
    ))

    application.add_error_handler(error_handler)
    return application
