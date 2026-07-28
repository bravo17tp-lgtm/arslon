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
    """Har yakshanba 21:00da — har bir juftlikka o'z haftalik xulosasini yuboradi."""
    cutoff_date = (date.today() - timedelta(days=7)).isoformat()
    cutoff_dt = cutoff_date + " 00:00:00"

    paired_users = [u for u in db.approved_users() if u["relationship_id"]]
    seen_relationships = set()

    for user in paired_users:
        rel_id = user["relationship_id"]
        if rel_id in seen_relationships:
            continue
        seen_relationships.add(rel_id)

        partner = db.partner_of(user["user_id"])
        pair_users = [user] + ([partner] if partner else [])

        journal_n = db.journal_count_since(rel_id, cutoff_dt)
        plans_n = db.plans_completed_since(rel_id, cutoff_dt)

        mood_lines = []
        for u in pair_users:
            common = db.most_common_mood_since(u["user_id"], cutoff_date)
            if common:
                mood_lines.append(f"{u['name']}: {common}")

        text = (
            "📊 *Haftalik xulosa*\n\n"
            f"Bu hafta {journal_n} ta xotira qo'shildi\n"
            f"{plans_n} ta reja bajarildi\n"
        )
        if mood_lines:
            text += "Eng ko'p bo'lgan kayfiyat — " + ", ".join(mood_lines) + "\n"
        text += "\nKeyingi hafta ham chiroyli xotiralar bilan to'lsin 💛"

        for u in pair_users:
            try:
                await context.bot.send_message(u["user_id"], text, parse_mode="Markdown")
            except Exception:
                pass
