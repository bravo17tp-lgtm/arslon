"""
Sevgi Mini App — ma'lumotlar qatlami (PostgreSQL / Supabase).

Arxitektura: har bir Telegram foydalanuvchisi mustaqil ro'yxatdan o'tadi.
Ikki foydalanuvchi taklif kodi orqali bog'lanib, bitta "relationship"
(juftlik) hosil qiladi. Barcha umumiy ma'lumotlar (xotiralar, kayfiyat,
rejalar, sevgi xatlari, maxsus kunlar) shu relationship_id orqali
ajratiladi — bir juftlik boshqasining ma'lumotini hech qachon ko'rmaydi.
"""

import json
import logging
import os
import random
import string
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

logger = logging.getLogger("sevgi.db")

DATABASE_URL = os.environ["DATABASE_URL"]

_pool_kwargs = {"cursor_factory": psycopg2.extras.RealDictCursor}
if "sslmode" not in DATABASE_URL:
    _pool_kwargs["sslmode"] = "require"

_pool = pg_pool.ThreadedConnectionPool(1, 10, dsn=DATABASE_URL, **_pool_kwargs)


class _ConnWrapper:
    """sqlite3.Connection.execute() uslubiga o'xshash qulay wrapper."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        return cur


@contextmanager
def get_conn():
    conn = _pool.getconn()
    try:
        wrapper = _ConnWrapper(conn)
        yield wrapper
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


# ============================================================
# Sxema
# ============================================================

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS relationships (
            id SERIAL PRIMARY KEY,
            invite_code TEXT UNIQUE NOT NULL,
            user_a_id BIGINT,
            user_b_id BIGINT,
            started_at DATE,
            created_at TIMESTAMPTZ DEFAULT now()
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT,
            language_code TEXT,
            status TEXT DEFAULT 'approved',
            is_admin BOOLEAN DEFAULT FALSE,
            relationship_id INTEGER REFERENCES relationships(id),
            request_count INTEGER DEFAULT 1,
            joined_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            last_active TIMESTAMPTZ,
            open_count INTEGER DEFAULT 0
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS journal (
            id SERIAL PRIMARY KEY,
            relationship_id INTEGER NOT NULL REFERENCES relationships(id),
            author_id BIGINT NOT NULL,
            text TEXT,
            photo_path TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS moods (
            id SERIAL PRIMARY KEY,
            relationship_id INTEGER NOT NULL REFERENCES relationships(id),
            user_id BIGINT NOT NULL,
            mood_date DATE NOT NULL,
            emoji TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(user_id, mood_date)
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS plans (
            id SERIAL PRIMARY KEY,
            relationship_id INTEGER NOT NULL REFERENCES relationships(id),
            author_id BIGINT NOT NULL,
            text TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT now(),
            completed_at TIMESTAMPTZ
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            answer_date DATE NOT NULL,
            question TEXT,
            answer TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(user_id, answer_date)
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS special_dates (
            id SERIAL PRIMARY KEY,
            relationship_id INTEGER NOT NULL REFERENCES relationships(id),
            author_id BIGINT,
            label TEXT NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            year INTEGER,
            created_at TIMESTAMPTZ DEFAULT now()
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
            id SERIAL PRIMARY KEY,
            admin_id BIGINT,
            admin_name TEXT,
            action TEXT,
            target_id BIGINT,
            detail TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )""")

        # Indexlar
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_relationship ON users(relationship_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_rel ON journal(relationship_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_moods_rel_date ON moods(relationship_id, mood_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_rel ON plans(relationship_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_special_dates_rel ON special_dates(relationship_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_logs(created_at)")
    logger.info("Postgres sxemasi tayyor.")


# ============================================================
# Foydalanuvchilar
# ============================================================

def create_user(user_id: int, name: str, username: str = None, status: str = "approved", is_admin: bool = False):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (user_id, name, username, status, is_admin) VALUES (%s,%s,%s,%s,%s) "
            "ON CONFLICT (user_id) DO NOTHING",
            (user_id, name, username, status, is_admin),
        )


def get_user(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=%s", (user_id,)).fetchone()


def touch_user_activity(user_id: int, username: str = None):
    with get_conn() as conn:
        if username:
            conn.execute(
                "UPDATE users SET last_active=now(), open_count=COALESCE(open_count,0)+1, "
                "username=%s, updated_at=now() WHERE user_id=%s",
                (username, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET last_active=now(), open_count=COALESCE(open_count,0)+1, "
                "updated_at=now() WHERE user_id=%s",
                (user_id,),
            )


def set_admin(user_id: int, is_admin: bool):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_admin=%s, updated_at=now() WHERE user_id=%s", (is_admin, user_id))


def set_user_status(user_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET status=%s, updated_at=now() WHERE user_id=%s", (status, user_id))


def unban_user(user_id: int):
    set_user_status(user_id, "approved")


def resend_request(user_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET status='pending', request_count=COALESCE(request_count,0)+1, updated_at=now() "
            "WHERE user_id=%s", (user_id,),
        )


# ============================================================
# Juftlik bog'lash (pairing)
# ============================================================

def _gen_invite_code() -> str:
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # chalkashadigan 0/O/1/I olib tashlangan
    return "".join(random.choices(alphabet, k=6))


def create_relationship(owner_id: int):
    """Yangi juftlik yaratadi va owner'ni unga bog'laydi. Taklif kodini qaytaradi."""
    with get_conn() as conn:
        for _ in range(5):
            code = _gen_invite_code()
            exists = conn.execute("SELECT 1 FROM relationships WHERE invite_code=%s", (code,)).fetchone()
            if not exists:
                break
        row = conn.execute(
            "INSERT INTO relationships (invite_code, user_a_id) VALUES (%s,%s) RETURNING *",
            (code, owner_id),
        ).fetchone()
        conn.execute("UPDATE users SET relationship_id=%s, updated_at=now() WHERE user_id=%s", (row["id"], owner_id))
        return row


def join_relationship(user_id: int, invite_code: str):
    """Kod bo'yicha juftlikka qo'shiladi. Muvaffaqiyatli bo'lsa relationship qaytaradi, aks holda None."""
    invite_code = (invite_code or "").strip().upper()
    with get_conn() as conn:
        rel = conn.execute("SELECT * FROM relationships WHERE invite_code=%s", (invite_code,)).fetchone()
        if not rel:
            return None
        if rel["user_a_id"] == user_id or rel["user_b_id"] == user_id:
            return rel  # allaqachon shu juftlikda
        if rel["user_b_id"] is not None:
            return None  # joy band
        conn.execute("UPDATE relationships SET user_b_id=%s WHERE id=%s", (user_id, rel["id"]))
        conn.execute("UPDATE users SET relationship_id=%s, updated_at=now() WHERE user_id=%s", (rel["id"], user_id))
        return conn.execute("SELECT * FROM relationships WHERE id=%s", (rel["id"],)).fetchone()


def get_relationship(relationship_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM relationships WHERE id=%s", (relationship_id,)).fetchone()


def partner_of(user_id: int):
    with get_conn() as conn:
        user = conn.execute("SELECT relationship_id FROM users WHERE user_id=%s", (user_id,)).fetchone()
        if not user or not user["relationship_id"]:
            return None
        rel = conn.execute("SELECT * FROM relationships WHERE id=%s", (user["relationship_id"],)).fetchone()
        if not rel:
            return None
        partner_id = rel["user_b_id"] if rel["user_a_id"] == user_id else rel["user_a_id"]
        if not partner_id:
            return None
        return conn.execute("SELECT * FROM users WHERE user_id=%s", (partner_id,)).fetchone()


def set_relationship_started_at(relationship_id: int, value: str):
    with get_conn() as conn:
        conn.execute("UPDATE relationships SET started_at=%s WHERE id=%s", (value, relationship_id))


# ============================================================
# Sozlamalar (kalit-qiymat, umumiy)
# ============================================================

def get_setting(key: str):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=%s", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (%s,%s) "
            "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
            (key, value),
        )


def get_json_setting(key: str):
    raw = get_setting(key)
    return json.loads(raw) if raw else None


def set_json_setting(key: str, value):
    set_setting(key, json.dumps(value, ensure_ascii=False))


# ============================================================
# Kundalik (xotiralar)
# ============================================================

def add_journal(relationship_id: int, author_id: int, text: str, photo_path: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO journal (relationship_id, author_id, text, photo_path) VALUES (%s,%s,%s,%s)",
            (relationship_id, author_id, text, photo_path),
        )


def recent_journal(relationship_id: int, limit: int = 30):
    with get_conn() as conn:
        return conn.execute(
            "SELECT j.*, u.name AS name FROM journal j JOIN users u ON u.user_id=j.author_id "
            "WHERE j.relationship_id=%s ORDER BY j.created_at DESC LIMIT %s",
            (relationship_id, limit),
        ).fetchall()


def journal_count(relationship_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM journal WHERE relationship_id=%s", (relationship_id,)
        ).fetchone()["c"]


def journal_count_since(relationship_id: int, cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM journal WHERE relationship_id=%s AND created_at >= %s",
            (relationship_id, cutoff_iso),
        ).fetchone()["c"]


def plans_completed_since(relationship_id: int, cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM plans WHERE relationship_id=%s AND done=TRUE AND completed_at >= %s",
            (relationship_id, cutoff_iso),
        ).fetchone()["c"]


def most_common_mood_since(user_id: int, cutoff_date: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT emoji, COUNT(*) c FROM moods WHERE user_id=%s AND mood_date >= %s "
            "GROUP BY emoji ORDER BY c DESC LIMIT 1",
            (user_id, cutoff_date),
        ).fetchone()
        return row["emoji"] if row else None


# ============================================================
# Kayfiyat
# ============================================================

def set_mood(relationship_id: int, user_id: int, mood_date: str, emoji: str, note: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO moods (relationship_id, user_id, mood_date, emoji, note) VALUES (%s,%s,%s,%s,%s) "
            "ON CONFLICT (user_id, mood_date) DO UPDATE SET emoji=EXCLUDED.emoji, note=EXCLUDED.note",
            (relationship_id, user_id, mood_date, emoji, note),
        )


def get_mood(user_id: int, mood_date: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM moods WHERE user_id=%s AND mood_date=%s", (user_id, mood_date)
        ).fetchone()


def mood_history(user_id: int, days: int = 30):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM moods WHERE user_id=%s ORDER BY mood_date DESC LIMIT %s", (user_id, days)
        ).fetchall()


# ============================================================
# Rejalar
# ============================================================

def add_plan(relationship_id: int, author_id: int, text: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO plans (relationship_id, author_id, text) VALUES (%s,%s,%s)",
            (relationship_id, author_id, text),
        )


def list_plans(relationship_id: int, only_open: bool = True):
    with get_conn() as conn:
        if only_open:
            return conn.execute(
                "SELECT * FROM plans WHERE relationship_id=%s AND done=FALSE ORDER BY created_at DESC",
                (relationship_id,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM plans WHERE relationship_id=%s ORDER BY created_at DESC", (relationship_id,)
        ).fetchall()


def complete_plan(plan_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE plans SET done=TRUE, completed_at=now() WHERE id=%s", (plan_id,))


# ============================================================
# Kun savoli
# ============================================================

def save_answer(user_id: int, answer_date: str, question: str, answer: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO answers (user_id, answer_date, question, answer) VALUES (%s,%s,%s,%s) "
            "ON CONFLICT (user_id, answer_date) DO UPDATE SET answer=EXCLUDED.answer, question=EXCLUDED.question",
            (user_id, answer_date, question, answer),
        )


def get_answer(user_id: int, answer_date: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM answers WHERE user_id=%s AND answer_date=%s", (user_id, answer_date)
        ).fetchone()


# ============================================================
# Maxsus kunlar
# ============================================================

def list_special_dates(relationship_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM special_dates WHERE relationship_id=%s ORDER BY month, day", (relationship_id,)
        ).fetchall()


def add_special_date(relationship_id: int, author_id: int, label: str, month: int, day: int, year: int = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO special_dates (relationship_id, author_id, label, month, day, year) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (relationship_id, author_id, label, month, day, year),
        )


def delete_special_date(date_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM special_dates WHERE id=%s", (date_id,))


# ============================================================
# Admin — global (barcha foydalanuvchilar bo'yicha)
# ============================================================

def pending_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='pending' ORDER BY joined_at DESC").fetchall()


def approved_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='approved' ORDER BY joined_at DESC").fetchall()


def denied_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='denied' ORDER BY joined_at DESC").fetchall()


def banned_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='banned' ORDER BY joined_at DESC").fetchall()


def all_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()


def admin_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE is_admin=TRUE ORDER BY joined_at").fetchall()


def search_user(query: str):
    q = f"%{query.strip()}%"
    with get_conn() as conn:
        if query.strip().isdigit():
            return conn.execute(
                "SELECT * FROM users WHERE user_id=%s OR name ILIKE %s OR username ILIKE %s LIMIT 30",
                (int(query.strip()), q, q),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM users WHERE name ILIKE %s OR username ILIKE %s LIMIT 30", (q, q)
        ).fetchall()


def user_statistics():
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status='approved') AS approved,
                COUNT(*) FILTER (WHERE status='pending') AS pending,
                COUNT(*) FILTER (WHERE status='denied') AS denied,
                COUNT(*) FILTER (WHERE status='banned') AS banned,
                COUNT(*) FILTER (WHERE is_admin=TRUE) AS admins
            FROM users
        """).fetchone()
        return dict(row)


def new_users_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) c FROM users WHERE joined_at >= %s", (cutoff_iso,)).fetchone()["c"]


def active_users_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) c FROM users WHERE last_active >= %s", (cutoff_iso,)).fetchone()["c"]


def most_active_users(limit: int = 10):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE status='approved' ORDER BY open_count DESC NULLS LAST LIMIT %s", (limit,)
        ).fetchall()


def log_admin_action(admin_id: int, admin_name: str, action: str, target_id: int = None, detail: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO admin_logs (admin_id, admin_name, action, target_id, detail) VALUES (%s,%s,%s,%s,%s)",
            (admin_id, admin_name, action, target_id, detail),
        )


def recent_admin_logs(limit: int = 30):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT %s", (limit,)).fetchall()
