"""Telegram Mini App initData ni tekshirish (autentifikatsiya)."""

import hashlib
import hmac
import json
import os
import time
import urllib.parse

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


def verify_init_data(init_data: str, max_age_seconds: int = 86400):
    """
    Telegram yuborgan initData satrini tekshiradi.
    Muvaffaqiyatli bo'lsa foydalanuvchi ma'lumotini (dict) qaytaradi, aks holda None.
    """
    if not init_data or not BOT_TOKEN:
        return None
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = int(parsed.get("auth_date", "0"))
    if max_age_seconds and (time.time() - auth_date) > max_age_seconds:
        return None

    user_raw = parsed.get("user")
    if not user_raw:
        return None
    return json.loads(user_raw)
