"""Rejalashtirilgan vazifalar: kunlik eslatma va haftalik xulosa."""

from datetime import date, timedelta

from telegram.ext import ContextTypes

from . import db


def today():
    return date.today().isoformat()


async def daily_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni 21:00da — agar kayfiyat belgilanmagan bo'lsa, eslatadi."""
    for user in db.approved_users():
        mood = db.get_mood(user["user_id"], today())
        if not mood:
            try:
                await context.bot.send_message(
                    user["user_id"],
                    "🌙 Bugungi kayfiyatingizni hali belgilamadingiz. Ilovani ochib, bir necha soniyada belgilab qo'ying 😊",
                )
            except Exception:
                pass


async def weekly_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """Har yakshanba 21:00da — haftalik xulosa yuboradi."""
    cutoff_date = (date.today() - timedelta(days=7)).isoformat()
    cutoff_dt = (date.today() - timedelta(days=7)).isoformat() + " 00:00:00"

    journal_n = db.journal_count_since(cutoff_dt)
    plans_n = db.plans_completed_since(cutoff_dt)

    users = db.approved_users()
    mood_lines = []
    for user in users:
        common = db.most_common_mood_since(user["user_id"], cutoff_date)
        if common:
            mood_lines.append(f"{user['name']}: {common}")

    text = (
        "📊 *Haftalik xulosa*\n\n"
        f"Bu hafta {journal_n} ta xotira qo'shildi\n"
        f"{plans_n} ta reja bajarildi\n"
    )
    if mood_lines:
        text += "Eng ko'p bo'lgan kayfiyat — " + ", ".join(mood_lines) + "\n"
    text += "\nKeyingi hafta ham chiroyli xotiralar bilan to'lsin 💛"

    for user in users:
        try:
            await context.bot.send_message(user["user_id"], text, parse_mode="Markdown")
        except Exception:
            pass
