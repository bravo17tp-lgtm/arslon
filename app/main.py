"""
Sevgi Mini App — FastAPI backend.
Bitta jarayonda: REST API + statik frontend + Telegram bot (polling) birga ishlaydi.
Ko'p foydalanuvchili (multi-user) arxitektura: har bir Telegram foydalanuvchisi
mustaqil ro'yxatdan o'tadi va taklif kodi orqali sherigi bilan bog'lanadi.
"""

import asyncio
import calendar
import logging
import os
from datetime import date, datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Request, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from telegram import Update

from . import db
from . import auth
from . import storage
from . content import MOOD_EMOJIS, QUESTIONS, QUOTES, LOVE_LANGUAGES, LOVE_TEST_QUESTIONS, THEMES
from . telegram_bot import build_bot_app, BOT_TOKEN
from . jobs import daily_reminder_job, weekly_summary_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sevgi.main")

BASE_DIR = Path(__file__).parent
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
TASHKENT = ZoneInfo("Asia/Tashkent")

app = FastAPI(title="Sevgi Mini App")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

bot_app = build_bot_app()


APP_URL = os.environ.get("APP_URL", "")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Kutilmagan xato: %s %s", request.url.path, exc, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Serverda kutilmagan xatolik yuz berdi."})


@app.get("/health")
def health():
    """Tashqi keep-alive xizmatlar (masalan cron-job.org) shu manzilni davriy chaqirib,
    Render'ning bepul tarifida serverni uxlab qolishdan, va bazaga ulanishlarning
    "jim turib" uzilib qolishidan saqlaydi."""
    try:
        db.get_setting("__healthcheck__")
    except Exception as e:
        logger.warning("Health check DB tekshiruvi muvaffaqiyatsiz: %s", e)
    return {"ok": True}


@app.post("/telegram-webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """Telegram har bir yangi xabarni shu manzilga POST qiladi.
    Bu — polling'dan farqli o'laroq — kiruvchi so'rov bo'lgani uchun,
    Render uxlab qolgan bo'lsa ham serverni avtomatik uyg'otadi."""
    if token != BOT_TOKEN:
        raise HTTPException(403, "Forbidden")
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


@app.on_event("startup")
async def startup():
    await db_call(db.init_db)
    await bot_app.initialize()
    await bot_app.start()

    if APP_URL:
        webhook_url = f"{APP_URL.rstrip('/')}/telegram-webhook/{BOT_TOKEN}"
        try:
            await bot_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
            logger.info("Webhook o'rnatildi: %s", webhook_url)
        except Exception as e:
            logger.error("Webhook o'rnatib bo'lmadi: %s", e)
    else:
        logger.warning("APP_URL bo'sh — webhook o'rnatilmadi. Uni Render Environment'da to'ldiring.")

    bot_app.job_queue.run_daily(
        daily_reminder_job, time=dtime(21, 0, tzinfo=TASHKENT), name="daily_reminder"
    )
    bot_app.job_queue.run_daily(
        weekly_summary_job, time=dtime(21, 0, tzinfo=TASHKENT), days=(6,), name="weekly_summary"
    )


@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
    await bot_app.shutdown()


# ---------- Auth yordamchisi ----------

def current_user(x_telegram_init_data: str = Header(None)):
    tg_user = auth.verify_init_data(x_telegram_init_data or "")
    if not tg_user:
        raise HTTPException(401, "Yaroqsiz Telegram autentifikatsiyasi")
    return tg_user


def require_approved_user(x_telegram_init_data: str = Header(None)):
    """Foydalanuvchi platformaga kira olishini tekshiradi (ban qilinmagan bo'lishi kerak)."""
    tg_user = current_user(x_telegram_init_data)
    user = db.get_user(tg_user["id"])
    if not user or user["status"] == "banned":
        raise HTTPException(403, "Kirish rad etildi")
    return user


def require_paired_user(x_telegram_init_data: str = Header(None)):
    """Sheriklar bog'langan (juftlik hosil bo'lgan) foydalanuvchini talab qiladi."""
    user = require_approved_user(x_telegram_init_data)
    if not user["relationship_id"]:
        raise HTTPException(409, "Hali sherigingiz bilan bog'lanmagansiz")
    return user


def today():
    return date.today().isoformat()


async def db_call(fn, *args, **kwargs):
    """Bloklovchi (sinxron) db.py chaqiruvlarini alohida threadda bajaradi — async endpointlar uchun."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ---------- Auth / ro'yxatdan o'tish ----------

@app.post("/api/auth")
async def api_auth(x_telegram_init_data: str = Header(None)):
    tg_user = current_user(x_telegram_init_data)
    user_id = tg_user["id"]
    name = tg_user.get("first_name", "Foydalanuvchi")
    user = await db_call(db.get_user, user_id)

    if user is None:
        is_admin = user_id == ADMIN_ID
        await db_call(db.create_user, user_id, name, username=tg_user.get("username"), status="approved", is_admin=is_admin)
        await db_call(db.create_relationship, user_id)
        user = await db_call(db.get_user, user_id)

    if user["status"] == "banned":
        return {"status": "banned", "name": user["name"]}

    if not user["relationship_id"]:
        await db_call(db.create_relationship, user_id)
        user = await db_call(db.get_user, user_id)

    await db_call(db.touch_user_activity, user_id, tg_user.get("username"))
    paired = bool(user["relationship_id"])
    return {"status": "approved", "name": user["name"], "paired": paired}


# ---------- Juftlik bog'lash (pairing) ----------

@app.get("/api/pair/status")
def pair_status(x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    if not user["relationship_id"]:
        return {"paired": False}
    partner = db.partner_of(user["user_id"])
    rel = db.get_relationship(user["relationship_id"])
    return {
        "paired": bool(partner),
        "invite_code": rel["invite_code"] if rel and not partner else None,
        "partner_name": partner["name"] if partner else None,
    }


@app.post("/api/pair/create")
def pair_create(x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    if user["relationship_id"]:
        rel = db.get_relationship(user["relationship_id"])
        return {"invite_code": rel["invite_code"]}
    rel = db.create_relationship(user["user_id"])
    return {"invite_code": rel["invite_code"]}


@app.post("/api/pair/join")
async def pair_join(code: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_approved_user, x_telegram_init_data)
    if await db_call(db.partner_of, user["user_id"]):
        raise HTTPException(400, "Siz allaqachon sherigingiz bilan bog'langansiz")
    rel = await db_call(db.join_relationship, user["user_id"], code)
    if rel == "own_code":
        raise HTTPException(400, "Bu sizning o'z kodingiz")
    if not rel:
        raise HTTPException(400, "Kod noto'g'ri yoki band")
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], f"💞 {user['name']} taklifingizni qabul qildi! Endi bog'langansiz.")
        except Exception:
            pass
    return {"ok": True, "partner_name": partner["name"] if partner else None}


# ---------- Bosh sahifa holati ----------

def compute_days_together(anniversary: str):
    if not anniversary:
        return None
    if isinstance(anniversary, date):
        d0 = anniversary
    else:
        d0 = date.fromisoformat(str(anniversary))
    d1 = date.today()
    years = d1.year - d0.year
    months = d1.month - d0.month
    days = d1.day - d0.day
    if days < 0:
        months -= 1
        prev_month = d1.month - 1 or 12
        prev_year = d1.year if d1.month > 1 else d1.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    total_days = (d1 - d0).days
    return {"years": years, "months": months, "days": days, "total_days": total_days}


def next_special_date(rows):
    today_d = date.today()
    best = None
    for r in rows:
        year = r["year"] or today_d.year
        try:
            cand = date(year, r["month"], r["day"])
        except ValueError:
            continue
        if cand < today_d:
            cand = date(today_d.year + 1, r["month"], r["day"])
        days_left = (cand - today_d).days
        if best is None or days_left < best["days_left"]:
            best = {"label": r["label"], "date": cand.isoformat(), "days_left": days_left}
    return best


@app.get("/api/state")
def api_state(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    rel_id = user["relationship_id"]
    partner = db.partner_of(user["user_id"])
    rel = db.get_relationship(rel_id)

    q_idx = date.today().timetuple().tm_yday % len(QUESTIONS)
    question = QUESTIONS[q_idx]
    my_answer = db.get_answer(user["user_id"], today())
    partner_answer = db.get_answer(partner["user_id"], today()) if partner else None

    my_mood = db.get_mood(user["user_id"], today())
    partner_mood = db.get_mood(partner["user_id"], today()) if partner else None

    specials = db.list_special_dates(rel_id)
    upcoming = next_special_date(specials)

    return {
        "name": user["name"],
        "partner_name": partner["name"] if partner else None,
        "together": compute_days_together(rel["started_at"] if rel else None),
        "quote": QUOTES[date.today().toordinal() % len(QUOTES)],
        "question": question,
        "my_answer": my_answer["answer"] if my_answer else None,
        "partner_answer": partner_answer["answer"] if partner_answer else None,
        "my_mood": my_mood["emoji"] if my_mood else None,
        "partner_mood": partner_mood["emoji"] if partner_mood else None,
        "upcoming_special": upcoming,
        "mood_emojis": MOOD_EMOJIS,
    }


# ---------- Kayfiyat ----------

@app.post("/api/mood")
async def api_set_mood(emoji: str = Form(...), note: str = Form(""), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    await db_call(db.set_mood, user["relationship_id"], user["user_id"], today(), emoji, note or None)
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], f"😊 Sherigingiz kayfiyatini belgiladi: {emoji}")
        except Exception:
            pass
    return {"ok": True}


@app.get("/api/moods")
def api_moods(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    partner = db.partner_of(user["user_id"])
    return {
        "mine": [dict(r) for r in db.mood_history(user["user_id"], 30)],
        "partner": [dict(r) for r in db.mood_history(partner["user_id"], 30)] if partner else [],
        "partner_name": partner["name"] if partner else None,
    }


# ---------- Kundalik ----------

@app.post("/api/journal")
async def api_add_journal(
    text: str = Form(""),
    title: str = Form(""),
    location: str = Form(""),
    hashtags: str = Form(""),
    is_important: bool = Form(False),
    photo: UploadFile = File(None),
    x_telegram_init_data: str = Header(None),
):
    user = await db_call(require_paired_user, x_telegram_init_data)
    photo_url = None
    media_type = "text"
    if photo is not None and photo.filename:
        content = await photo.read()
        photo_url = await storage.upload_bytes(content, photo.filename, photo.content_type)
        media_type = "video" if (photo.content_type or "").startswith("video") else "photo"
    journal_id = await db_call(
        db.add_journal, user["relationship_id"], user["user_id"], text, photo_url,
        title or None, media_type, location or None, hashtags or None, is_important,
    )
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], "📔 Kundalikka yangi xotira qo'shildi!")
        except Exception:
            pass
    return {"ok": True, "id": journal_id}


def _serialize_journal(e, reactions, comment_counts):
    r = reactions.get(e["id"], {"count": 0, "liked": False})
    return {
        "id": e["id"],
        "author_id": e["author_id"],
        "name": e["name"],
        "title": e["title"],
        "text": e["text"],
        "photo_url": e["photo_path"],
        "media_type": e["media_type"] or "text",
        "location": e["location"],
        "hashtags": e["hashtags"],
        "is_important": bool(e["is_important"]),
        "created_at": e["created_at"],
        "like_count": r["count"],
        "liked_by_me": r["liked"],
        "comment_count": comment_counts.get(e["id"], 0),
    }


@app.get("/api/journal")
async def api_journal(x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entries = await db_call(db.recent_journal, user["relationship_id"], 100)
    reactions = await db_call(db.journal_reaction_summaries, user["relationship_id"], user["user_id"])
    comment_counts = await db_call(db.journal_comment_counts, user["relationship_id"])
    return [_serialize_journal(e, reactions, comment_counts) for e in entries]


@app.get("/api/journal/{journal_id}")
async def api_journal_detail(journal_id: int, x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entry = await db_call(db.get_journal_entry, journal_id)
    if not entry or entry["relationship_id"] != user["relationship_id"]:
        raise HTTPException(404, "Xotira topilmadi")
    reaction = await db_call(db.journal_reaction_summary, journal_id, user["user_id"])
    comments = await db_call(db.list_journal_comments, journal_id)
    return {
        **_serialize_journal(entry, {journal_id: reaction}, {}),
        "comment_count": len(comments),
        "comments": [
            {"id": c["id"], "author_id": c["author_id"], "name": c["name"], "text": c["text"], "created_at": c["created_at"]}
            for c in comments
        ],
    }


@app.put("/api/journal/{journal_id}")
async def api_journal_edit(
    journal_id: int,
    title: str = Form(""),
    text: str = Form(""),
    location: str = Form(""),
    hashtags: str = Form(""),
    is_important: bool = Form(False),
    x_telegram_init_data: str = Header(None),
):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entry = await db_call(db.get_journal_entry, journal_id)
    if not entry or entry["relationship_id"] != user["relationship_id"]:
        raise HTTPException(404, "Xotira topilmadi")
    await db_call(db.update_journal_entry, journal_id, title or None, text, is_important, location or None, hashtags or None)
    return {"ok": True}


@app.delete("/api/journal/{journal_id}")
async def api_journal_delete(journal_id: int, x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entry = await db_call(db.get_journal_entry, journal_id)
    if not entry or entry["relationship_id"] != user["relationship_id"]:
        raise HTTPException(404, "Xotira topilmadi")
    await db_call(db.delete_journal_entry, journal_id)
    return {"ok": True}


@app.post("/api/journal/{journal_id}/like")
async def api_journal_like(journal_id: int, x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entry = await db_call(db.get_journal_entry, journal_id)
    if not entry or entry["relationship_id"] != user["relationship_id"]:
        raise HTTPException(404, "Xotira topilmadi")
    liked = await db_call(db.toggle_journal_reaction, journal_id, user["user_id"])
    if liked:
        partner = await db_call(db.partner_of, user["user_id"])
        if partner and entry["author_id"] == partner["user_id"]:
            try:
                await bot_app.bot.send_message(partner["user_id"], f"❤️ {user['name']} xotirangizni yoqtirdi!")
            except Exception:
                pass
    summary = await db_call(db.journal_reaction_summary, journal_id, user["user_id"])
    return summary


@app.post("/api/journal/{journal_id}/bookmark")
async def api_journal_bookmark(journal_id: int, x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    saved = await db_call(db.toggle_journal_bookmark, journal_id, user["user_id"])
    return {"saved": saved}


@app.post("/api/journal/{journal_id}/comments")
async def api_journal_add_comment(journal_id: int, text: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    entry = await db_call(db.get_journal_entry, journal_id)
    if not entry or entry["relationship_id"] != user["relationship_id"]:
        raise HTTPException(404, "Xotira topilmadi")
    await db_call(db.add_journal_comment, journal_id, user["user_id"], text)
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], f"💬 {user['name']} xotiraga izoh qoldirdi: {text[:80]}")
        except Exception:
            pass
    return {"ok": True}


# ---------- Rejalar ----------

@app.post("/api/plans")
async def api_add_plan(text: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    await db_call(db.add_plan, user["relationship_id"], user["user_id"], text)
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], "📝 Yangi reja qo'shildi!")
        except Exception:
            pass
    return {"ok": True}


@app.get("/api/plans")
def api_plans(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    return [dict(p) for p in db.list_plans(user["relationship_id"], only_open=True)]


@app.post("/api/plans/{plan_id}/done")
def api_plan_done(plan_id: int, x_telegram_init_data: str = Header(None)):
    require_paired_user(x_telegram_init_data)
    db.complete_plan(plan_id)
    return {"ok": True}


# ---------- Kun savoli ----------

@app.post("/api/question/answer")
async def api_answer_question(text: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    q_idx = date.today().timetuple().tm_yday % len(QUESTIONS)
    await db_call(db.save_answer, user["user_id"], today(), QUESTIONS[q_idx], text)
    partner = await db_call(db.partner_of, user["user_id"])
    if partner:
        try:
            await bot_app.bot.send_message(partner["user_id"], "❓ Sherigingiz bugungi savolga javob berdi!")
        except Exception:
            pass
    return {"ok": True}


# ---------- Sevgi xati ----------

@app.post("/api/love_note")
async def api_love_note(text: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = await db_call(require_paired_user, x_telegram_init_data)
    partner = await db_call(db.partner_of, user["user_id"])
    if not partner:
        raise HTTPException(400, "Sherigingiz hali qo'shilmagan")
    try:
        await bot_app.bot.send_message(partner["user_id"], f"💌 Sizga sevgi xati keldi:\n\n{text}")
    except Exception:
        raise HTTPException(500, "Yuborishda xatolik")
    return {"ok": True}


# ---------- Profil ----------

@app.get("/api/profile")
def api_profile(x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    partner = db.partner_of(user["user_id"])
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
        "joined_at": user["joined_at"],
        "open_count": user["open_count"] or 0,
        "partner_name": partner["name"] if partner else None,
    }


# ---------- Statistika ----------

@app.get("/api/stats")
def api_stats(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    rel = db.get_relationship(user["relationship_id"])
    return {
        "together": compute_days_together(rel["started_at"] if rel else None),
        "journal_count": db.journal_count(user["relationship_id"]),
    }


# ---------- Sozlamalar: sevgi sanasi ----------

@app.get("/api/settings/anniversary")
def get_anniversary(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    rel = db.get_relationship(user["relationship_id"])
    started = rel["started_at"] if rel else None
    return {"anniversary": started.isoformat() if started else None}


@app.post("/api/settings/anniversary")
def set_anniversary(value: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, "Noto'g'ri sana formati")
    db.set_relationship_started_at(user["relationship_id"], value)
    return {"ok": True}


# ---------- Sozlamalar: maxsus kunlar ----------

@app.get("/api/settings/special_dates")
def get_special_dates(x_telegram_init_data: str = Header(None)):
    user = require_paired_user(x_telegram_init_data)
    return [dict(r) for r in db.list_special_dates(user["relationship_id"])]


@app.post("/api/settings/special_dates")
def add_special_date(
    label: str = Form(...),
    month: int = Form(...),
    day: int = Form(...),
    year: int = Form(None),
    x_telegram_init_data: str = Header(None),
):
    user = require_paired_user(x_telegram_init_data)
    db.add_special_date(user["relationship_id"], user["user_id"], label, month, day, year)
    return {"ok": True}


@app.delete("/api/settings/special_dates/{date_id}")
def remove_special_date(date_id: int, x_telegram_init_data: str = Header(None)):
    require_paired_user(x_telegram_init_data)
    db.delete_special_date(date_id)
    return {"ok": True}


# ---------- Sozlamalar: sevgi tili testi ----------

@app.get("/api/settings/love_test/questions")
def love_test_questions(x_telegram_init_data: str = Header(None)):
    require_approved_user(x_telegram_init_data)
    return {"questions": LOVE_TEST_QUESTIONS, "languages": LOVE_LANGUAGES}


@app.post("/api/settings/love_test/submit")
def love_test_submit(answers: str = Form(...), x_telegram_init_data: str = Header(None)):
    """answers: vergul bilan ajratilgan kalitlar, masalan 'words,time,words,gifts,touch'"""
    user = require_approved_user(x_telegram_init_data)
    keys = answers.split(",")
    scores = {}
    for k in keys:
        k = k.strip()
        if k in LOVE_LANGUAGES:
            scores[k] = scores.get(k, 0) + 1
    top = max(scores, key=scores.get) if scores else None
    db.set_json_setting(f"love_test_{user['user_id']}", {"scores": scores, "top": top})
    return {"scores": scores, "top": top, "top_label": LOVE_LANGUAGES.get(top)}


@app.get("/api/settings/love_test/result")
def love_test_result(x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    partner = db.partner_of(user["user_id"])
    mine = db.get_json_setting(f"love_test_{user['user_id']}")
    theirs = db.get_json_setting(f"love_test_{partner['user_id']}") if partner else None
    return {
        "mine": mine,
        "mine_label": LOVE_LANGUAGES.get(mine["top"]) if mine else None,
        "partner": theirs,
        "partner_label": LOVE_LANGUAGES.get(theirs["top"]) if theirs else None,
        "partner_name": partner["name"] if partner else None,
    }


# ---------- Sozlamalar: tema ----------

@app.get("/api/settings/theme")
def get_theme(x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    stored = db.get_setting(f"theme_{user['user_id']}")
    return {"theme": stored or "tungi", "is_default": stored is None, "themes": THEMES}


@app.post("/api/settings/theme")
def set_theme(value: str = Form(...), x_telegram_init_data: str = Header(None)):
    user = require_approved_user(x_telegram_init_data)
    if value not in THEMES:
        raise HTTPException(400, "Noto'g'ri tema")
    db.set_setting(f"theme_{user['user_id']}", value)
    return {"ok": True}


# ---------- Statik frontend ----------

app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")
