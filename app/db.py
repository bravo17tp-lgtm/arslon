"""SQLite yordamchi funksiyalari — Sevgi Mini App uchun."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "love.db"
DB_PATH.parent.mkdir(exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT,
            language_code TEXT,
            status TEXT DEFAULT 'pending',
            is_admin INTEGER DEFAULT 0,
            request_count INTEGER DEFAULT 1,
            joined_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_active TEXT,
            open_count INTEGER DEFAULT 0
        )""")
        # Eski bazalarda yangi ustunlar bo'lmasligi mumkin — xavfsiz qo'shamiz
        existing_cols = {row["name"] for row in c.execute("PRAGMA table_info(users)").fetchall()}
        if "last_active" not in existing_cols:
            c.execute("ALTER TABLE users ADD COLUMN last_active TEXT")
        if "open_count" not in existing_cols:
            c.execute("ALTER TABLE users ADD COLUMN open_count INTEGER DEFAULT 0")
        c.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            admin_name TEXT,
            action TEXT,
            target_id INTEGER,
            detail TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            photo_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood_date TEXT,
            emoji TEXT,
            note TEXT,
            UNIQUE(user_id, mood_date)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_by INTEGER,
            text TEXT,
            done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            answer_date TEXT,
            question TEXT,
            answer TEXT,
            UNIQUE(user_id, answer_date)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS special_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_by INTEGER,
            label TEXT,
            month INTEGER,
            day INTEGER,
            year INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        # Indexlar — barcha jadvallar yaratilgandan keyin (tezkor qidiruv uchun)
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_journal_user ON journal(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_moods_user_date ON moods(user_id, mood_date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_logs(created_at)")


# ---------- users ----------

def get_user(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def create_user(user_id: int, name: str, username: str=None, language_code: str=None, status: str = "pending", is_admin: bool = False):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name, username, language_code, status, is_admin) VALUES (?,?,?,?,?,?)",
            (user_id, name, username, language_code, status, int(is_admin)),
        )


def set_user_status(user_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET status=?, updated_at=datetime('now') WHERE user_id=?", (status, user_id))


def pending_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='pending'").fetchall()


def approved_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='approved'").fetchall()


def partner_of(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE status='approved' AND user_id != ?", (user_id,)
        ).fetchall()
        return rows[0] if rows else None


# ---------- journal ----------

def add_journal(user_id: int, text: str, photo_path: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO journal (user_id, text, photo_path) VALUES (?,?,?)",
            (user_id, text, photo_path),
        )


def recent_journal(limit: int = 30):
    with get_conn() as conn:
        return conn.execute(
            "SELECT j.*, u.name FROM journal j JOIN users u ON j.user_id=u.user_id "
            "ORDER BY j.id DESC LIMIT ?", (limit,),
        ).fetchall()


def journal_count():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) c FROM journal").fetchone()["c"]


def journal_count_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM journal WHERE created_at >= ?", (cutoff_iso,)
        ).fetchone()["c"]


# ---------- moods ----------

def set_mood(user_id: int, mood_date: str, emoji: str, note: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO moods (user_id, mood_date, emoji, note) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, mood_date) DO UPDATE SET emoji=excluded.emoji, note=excluded.note",
            (user_id, mood_date, emoji, note),
        )


def get_mood(user_id: int, mood_date: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM moods WHERE user_id=? AND mood_date=?", (user_id, mood_date)
        ).fetchone()


def mood_history(user_id: int, limit: int = 30):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM moods WHERE user_id=? ORDER BY mood_date DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return list(reversed(rows))


def most_common_mood_since(user_id: int, cutoff_date: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT emoji, COUNT(*) c FROM moods WHERE user_id=? AND mood_date >= ? "
            "GROUP BY emoji ORDER BY c DESC LIMIT 1",
            (user_id, cutoff_date),
        ).fetchone()
        return row["emoji"] if row else None


# ---------- plans ----------

def add_plan(created_by: int, text: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO plans (created_by, text) VALUES (?,?)", (created_by, text))


def list_plans(only_open: bool = True):
    with get_conn() as conn:
        q = "SELECT p.*, u.name FROM plans p JOIN users u ON p.created_by=u.user_id"
        if only_open:
            q += " WHERE p.done=0"
        q += " ORDER BY p.id DESC"
        return conn.execute(q).fetchall()


def complete_plan(plan_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE plans SET done=1, completed_at=datetime('now') WHERE id=?", (plan_id,)
        )


def plans_completed_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM plans WHERE done=1 AND completed_at >= ?", (cutoff_iso,)
        ).fetchone()["c"]


# ---------- daily question ----------

def save_answer(user_id: int, answer_date: str, question: str, answer: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO answers (user_id, answer_date, question, answer) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, answer_date) DO UPDATE SET answer=excluded.answer",
            (user_id, answer_date, question, answer),
        )


def get_answer(user_id: int, answer_date: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM answers WHERE user_id=? AND answer_date=?", (user_id, answer_date)
        ).fetchone()


# ---------- special dates ----------

def add_special_date(created_by: int, label: str, month: int, day: int, year: int = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO special_dates (created_by, label, month, day, year) VALUES (?,?,?,?,?)",
            (created_by, label, month, day, year),
        )


def list_special_dates():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM special_dates ORDER BY id DESC").fetchall()


def delete_special_date(date_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM special_dates WHERE id=?", (date_id,))


# ---------- settings ----------

def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def get_setting(key: str):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def set_json_setting(key: str, value: dict):
    set_setting(key, json.dumps(value, ensure_ascii=False))


def get_json_setting(key: str):
    raw = get_setting(key)
    return json.loads(raw) if raw else None


def resend_request(user_id:int):
    with get_conn() as conn:
        conn.execute("""
        UPDATE users
        SET status='pending',
            request_count=COALESCE(request_count,1)+1,
            updated_at=datetime('now')
        WHERE user_id=?
        """,(user_id,))


# ---------- admin helpers ----------

def total_users():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]


def banned_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='banned' ORDER BY joined_at DESC").fetchall()


def denied_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE status='denied' ORDER BY joined_at DESC").fetchall()


def admin_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE is_admin=1").fetchall()


def all_users():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()


def search_user(query: str):
    with get_conn() as conn:
        q = f"%{query}%"
        return conn.execute(
            '''
            SELECT *
            FROM users
            WHERE
                CAST(user_id AS TEXT) LIKE ?
                OR name LIKE ?
                OR COALESCE(username,'') LIKE ?
            ORDER BY joined_at DESC
            ''',
            (q, q, q),
        ).fetchall()


def user_statistics():
    with get_conn() as conn:
        row = conn.execute(
            '''
            SELECT
                COUNT(*) total,
                SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) approved,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) pending,
                SUM(CASE WHEN status='denied' THEN 1 ELSE 0 END) denied,
                SUM(CASE WHEN status='banned' THEN 1 ELSE 0 END) banned,
                SUM(CASE WHEN is_admin=1 THEN 1 ELSE 0 END) admins
            FROM users
            '''
        ).fetchone()
        return dict(row)


def unban_user(user_id: int):
    set_user_status(user_id, "approved")


# ---------- faollik kuzatuvi ----------

def touch_user_activity(user_id: int, username: str = None):
    """Mini App ochilganda chaqiriladi: oxirgi faollik va ochilish sonini yangilaydi."""
    with get_conn() as conn:
        if username:
            conn.execute(
                "UPDATE users SET last_active=datetime('now'), open_count=COALESCE(open_count,0)+1, "
                "username=?, updated_at=datetime('now') WHERE user_id=?",
                (username, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET last_active=datetime('now'), open_count=COALESCE(open_count,0)+1, "
                "updated_at=datetime('now') WHERE user_id=?",
                (user_id,),
            )


# ---------- multi-admin ----------

def set_admin(user_id: int, is_admin: bool):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_admin=?, updated_at=datetime('now') WHERE user_id=?", (int(is_admin), user_id))


# ---------- admin loglar ----------

def log_admin_action(admin_id: int, admin_name: str, action: str, target_id: int = None, detail: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO admin_logs (admin_id, admin_name, action, target_id, detail) VALUES (?,?,?,?,?)",
            (admin_id, admin_name, action, target_id, detail),
        )


def recent_admin_logs(limit: int = 30):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


# ---------- analitika ----------

def new_users_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM users WHERE joined_at >= ?", (cutoff_iso,)
        ).fetchone()["c"]


def active_users_since(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) c FROM users WHERE last_active >= ?", (cutoff_iso,)
        ).fetchone()["c"]


def inactive_users(cutoff_iso: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE status='approved' AND (last_active IS NULL OR last_active < ?) "
            "ORDER BY last_active ASC", (cutoff_iso,)
        ).fetchall()


def most_active_users(limit: int = 10):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE status='approved' ORDER BY open_count DESC LIMIT ?", (limit,)
        ).fetchall()
