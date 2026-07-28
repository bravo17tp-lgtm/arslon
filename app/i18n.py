"""Bot xabarlari uchun oddiy i18n (uz / ru / en)."""

DEFAULT_LANG = "uz"
LANGS = ["uz", "ru", "en"]

LANG_NAMES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

T = {
    # ---------- umumiy tugmalar ----------
    "btn_open": {"uz": "💞 Ochish", "ru": "💞 Открыть", "en": "💞 Open"},
    "btn_add_partner": {"uz": "💌 Sherik qo'shish", "ru": "💌 Добавить партнёра", "en": "💌 Add partner"},
    "btn_settings": {"uz": "⚙️ Sozlamalar", "ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "btn_back": {"uz": "⬅️ Orqaga", "ru": "⬅️ Назад", "en": "⬅️ Back"},
    "btn_get_code": {"uz": "🔑 Taklif kodini olish", "ru": "🔑 Получить код приглашения", "en": "🔑 Get invite code"},
    "btn_enter_code": {"uz": "🔑 Kodni kiritish", "ru": "🔑 Ввести код", "en": "🔑 Enter code"},
    "btn_cancel": {"uz": "❌ Bekor qilish", "ru": "❌ Отмена", "en": "❌ Cancel"},
    "btn_language": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"},
    "btn_reset_data": {"uz": "🗑 Ma'lumotni o'chirish", "ru": "🗑 Удалить данные", "en": "🗑 Delete data"},
    "btn_change_partner": {"uz": "🔄 Sherikni almashtirish", "ru": "🔄 Сменить партнёра", "en": "🔄 Change partner"},
    "btn_cancel_invite": {"uz": "🔄 Taklifni bekor qilish", "ru": "🔄 Отменить приглашение", "en": "🔄 Cancel invite"},
    "btn_connect_partner": {"uz": "💌 Sherik bilan bog'lanish", "ru": "💌 Связаться с партнёром", "en": "💌 Connect with partner"},
    "btn_admin_panel": {"uz": "👑 Admin panel", "ru": "👑 Админ-панель", "en": "👑 Admin panel"},
    "btn_continue": {"uz": "Davom etish", "ru": "Продолжить", "en": "Continue"},
    "btn_yes_sure": {"uz": "✅ Ha, albatta", "ru": "✅ Да, конечно", "en": "✅ Yes, sure"},
    "btn_no_cancel": {"uz": "❌ Yo'q, bekor qilish", "ru": "❌ Нет, отмена", "en": "❌ No, cancel"},
    "btn_agree": {"uz": "✅ Roziman", "ru": "✅ Согласен(а)", "en": "✅ I agree"},
    "btn_disagree": {"uz": "❌ Rozi emasman", "ru": "❌ Не согласен(а)", "en": "❌ I disagree"},

    # ---------- /start ----------
    "welcome_new": {
        "uz": "Xush kelibsiz, {name}! 💞\n\nSevgi ilovasidan foydalanish uchun sherigingiz bilan bog'laning, "
              "yoki ilovani his qilib ko'rish uchun uni ochib ko'rishingiz mumkin 👇",
        "ru": "Добро пожаловать, {name}! 💞\n\nЧтобы пользоваться приложением Sevgi, свяжитесь с партнёром, "
              "или просто откройте приложение и осмотритесь 👇",
        "en": "Welcome, {name}! 💞\n\nTo use the Sevgi app, connect with your partner — "
              "or just open the app to explore it 👇",
    },
    "welcome_waiting": {
        "uz": "Sizning taklif kodingiz: `{code}`\n\nSherigingiz botga kirib shu kodni kiritishi bilan bog'lanasiz.\n\n"
              "Sherigingizni kutayotganda ilovani ochib ko'rishingiz ham mumkin 👇",
        "ru": "Ваш код приглашения: `{code}`\n\nКогда партнёр зайдёт в бота и введёт этот код, вы будете связаны.\n\n"
              "Пока ждёте партнёра, можно открыть приложение 👇",
        "en": "Your invite code: `{code}`\n\nOnce your partner enters the bot and submits this code, you'll be connected.\n\n"
              "While waiting, feel free to open the app 👇",
    },
    "welcome_paired": {
        "uz": "Xush kelibsiz, {name}! 🌷 Siz {partner} bilan bog'langansiz.",
        "ru": "Добро пожаловать, {name}! 🌷 Вы связаны с {partner}.",
        "en": "Welcome, {name}! 🌷 You're connected with {partner}.",
    },
    "banned": {
        "uz": "🚫 Siz bloklangansiz.",
        "ru": "🚫 Вы заблокированы.",
        "en": "🚫 You are banned.",
    },

    # ---------- Sherik qo'shish ----------
    "addpartner_title": {
        "uz": "💌 *Sherik qo'shish*\n\nTaklif kodi orqali sherigingiz bilan bog'laning:",
        "ru": "💌 *Добавить партнёра*\n\nСвяжитесь с партнёром при помощи кода приглашения:",
        "en": "💌 *Add partner*\n\nConnect with your partner using an invite code:",
    },
    "own_code_shown": {
        "uz": "✅ Sizning taklif kodingiz: `{code}`\n\nBuni sherigingizga yuboring. U botga kirib "
              "\"{enter_btn}\" tugmasi orqali shu kodni kiritsa, bog'lanasiz.",
        "ru": "✅ Ваш код приглашения: `{code}`\n\nОтправьте его партнёру. Когда он зайдёт в бота и введёт код "
              "через кнопку \"{enter_btn}\", вы будете связаны.",
        "en": "✅ Your invite code: `{code}`\n\nSend it to your partner. Once they enter the bot and submit the "
              "code via \"{enter_btn}\", you'll be connected.",
    },
    "ask_enter_code": {
        "uz": "🔑 Sherigingiz bergan 6 xonali kodni yuboring.",
        "ru": "🔑 Отправьте 6-значный код, который дал вам партнёр.",
        "en": "🔑 Send the 6-character code your partner gave you.",
    },
    "code_invalid": {
        "uz": "❗️ Kod noto'g'ri yoki band. Qaytadan urinib ko'ring:",
        "ru": "❗️ Код неверный или уже занят. Попробуйте снова:",
        "en": "❗️ The code is invalid or already taken. Please try again:",
    },
    "btn_retry": {"uz": "🔑 Qayta urinish", "ru": "🔑 Попробовать снова", "en": "🔑 Try again"},
    "joined_success": {
        "uz": "💞 Tabriklaymiz! Siz {partner} bilan bog'landingiz!",
        "ru": "💞 Поздравляем! Вы связаны с {partner}!",
        "en": "💞 Congratulations! You're now connected with {partner}!",
    },
    "partner_joined_notice": {
        "uz": "💞 {name} taklifingizni qabul qildi! Endi bog'langansiz.",
        "ru": "💞 {name} принял(а) ваше приглашение! Теперь вы связаны.",
        "en": "💞 {name} accepted your invite! You're now connected.",
    },
    "partner_fallback": {"uz": "sherigingiz", "ru": "партнёром", "en": "your partner"},

    # ---------- Sozlamalar ----------
    "settings_title": {
        "uz": "⚙️ *Sozlamalar*\n\nKerakli bo'limni tanlang:",
        "ru": "⚙️ *Настройки*\n\nВыберите нужный раздел:",
        "en": "⚙️ *Settings*\n\nChoose a section:",
    },
    "language_title": {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
        "en": "🌐 Choose a language:",
    },
    "language_set": {
        "uz": "✅ Til o'zgartirildi.",
        "ru": "✅ Язык изменён.",
        "en": "✅ Language updated.",
    },
    "not_admin": {
        "uz": "⛔ Siz admin emassiz.",
        "ru": "⛔ Вы не администратор.",
        "en": "⛔ You are not an admin.",
    },

    # ---------- Ma'lumotni o'chirish ----------
    "reset_confirm1": {
        "uz": "⚠️ *Diqqat!* Bu amal barcha xotiralar, kayfiyat tarixi, rejalar va maxsus kunlaringizni "
              "butunlay o'chiradi. Sherikligingiz saqlanib qoladi — faqat ma'lumotlar tozalanadi.\n\nDavom etasizmi?",
        "ru": "⚠️ *Внимание!* Это действие полностью удалит все воспоминания, историю настроения, планы и "
              "особые даты. Связь с партнёром сохранится — удалятся только данные.\n\nПродолжить?",
        "en": "⚠️ *Warning!* This will permanently delete all memories, mood history, plans and special dates. "
              "Your relationship link stays — only the data is cleared.\n\nContinue?",
    },
    "reset_confirm2": {
        "uz": "❗️ *So'nggi ogohlantirish.* Bu amalni ortga qaytarib bo'lmaydi — barcha ma'lumotlar butunlay yo'qoladi.\n\n"
              "Ishonchingiz komilmi?",
        "ru": "❗️ *Последнее предупреждение.* Это действие необратимо — все данные будут полностью удалены.\n\n"
              "Вы уверены?",
        "en": "❗️ *Final warning.* This cannot be undone — all data will be permanently lost.\n\nAre you sure?",
    },
    "reset_no_relationship": {
        "uz": "Hozircha aktiv juftlik topilmadi.",
        "ru": "Активная пара пока не найдена.",
        "en": "No active relationship found yet.",
    },
    "reset_done_alone": {
        "uz": "🗑 Ma'lumotlar tozalandi. Yangidan boshlashingiz mumkin!",
        "ru": "🗑 Данные удалены. Можете начать заново!",
        "en": "🗑 Data cleared. You can start fresh!",
    },
    "reset_sent_to_partner": {
        "uz": "⏳ So'rov sherigingizga yuborildi. U ham tasdiqlagach, ma'lumotlar tozalanadi.",
        "ru": "⏳ Запрос отправлен партнёру. После его подтверждения данные будут удалены.",
        "en": "⏳ Request sent to your partner. Once they confirm, the data will be cleared.",
    },
    "reset_ask_partner": {
        "uz": "⚠️ *{name}* barcha umumiy ma'lumotlaringizni (xotiralar, kayfiyat, rejalar, maxsus kunlar) "
              "butunlay tozalashni so'ramoqda.\n\nBunga roziimisiz?",
        "ru": "⚠️ *{name}* просит полностью удалить все ваши общие данные (воспоминания, настроение, планы, "
              "особые даты).\n\nВы согласны?",
        "en": "⚠️ *{name}* is asking to permanently clear all your shared data (memories, moods, plans, "
              "special dates).\n\nDo you agree?",
    },
    "reset_send_fail": {
        "uz": "Sherigingizga xabar yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
        "ru": "Не удалось отправить сообщение партнёру. Попробуйте позже.",
        "en": "Couldn't send a message to your partner. Please try again later.",
    },
    "reset_expired": {
        "uz": "Bu so'rov endi amal qilmaydi.",
        "ru": "Этот запрос больше не действителен.",
        "en": "This request is no longer valid.",
    },
    "reset_done": {
        "uz": "🗑 Ma'lumotlar tozalandi.",
        "ru": "🗑 Данные удалены.",
        "en": "🗑 Data cleared.",
    },
    "reset_approved_notice": {
        "uz": "✅ {name} rozi bo'ldi. Ma'lumotlar tozalandi.",
        "ru": "✅ {name} согласился(лась). Данные удалены.",
        "en": "✅ {name} agreed. Data has been cleared.",
    },
    "reset_cancelled": {
        "uz": "Bekor qilindi — ma'lumotlar tozalanmadi.",
        "ru": "Отменено — данные не удалены.",
        "en": "Cancelled — data was not cleared.",
    },
    "reset_denied_notice": {
        "uz": "❌ Sherigingiz ma'lumotlarni tozalashga rozi bo'lmadi.",
        "ru": "❌ Партнёр не согласился на удаление данных.",
        "en": "❌ Your partner did not agree to clear the data.",
    },

    # ---------- Sherikni almashtirish / bekor qilish ----------
    "unlink_confirm1": {
        "uz": "⚠️ *Diqqat!* Bu amal joriy bog'lanishni butunlay bekor qiladi. Agar sherigingiz allaqachon "
              "bog'langan bo'lsa, u ham ajraladi va ikkalangiz alohida yangi sherik bilan bog'lanishingiz "
              "kerak bo'ladi. Umumiy ma'lumotlar o'chirilmaydi, lekin unga hech kim kira olmay qoladi.\n\n"
              "Davom etasizmi?",
        "ru": "⚠️ *Внимание!* Это действие полностью разорвёт текущую связь. Если партнёр уже связан с вами, "
              "он тоже отсоединится, и вам обоим нужно будет связываться с новым партнёром заново. Общие данные "
              "не удаляются, но никто не сможет их видеть.\n\nПродолжить?",
        "en": "⚠️ *Warning!* This will completely break the current link. If your partner is already connected, "
              "they'll be disconnected too, and you'll both need to connect with a new partner. Shared data isn't "
              "deleted, but no one will be able to access it.\n\nContinue?",
    },
    "unlink_confirm2": {
        "uz": "❗️ *So'nggi ogohlantirish.* Aloqa uzilgach, qayta bog'lanish uchun yangi taklif kodi kerak bo'ladi.\n\n"
              "Ishonchingiz komilmi?",
        "ru": "❗️ *Последнее предупреждение.* После разрыва связи для повторного соединения понадобится новый код "
              "приглашения.\n\nВы уверены?",
        "en": "❗️ *Final warning.* Once disconnected, you'll need a new invite code to reconnect.\n\nAre you sure?",
    },
    "unlink_done_alone": {
        "uz": "🔄 Bekor qilindi. Qaytadan tanlang:",
        "ru": "🔄 Отменено. Выберите заново:",
        "en": "🔄 Cancelled. Please choose again:",
    },
    "unlink_sent_to_partner": {
        "uz": "⏳ So'rov sherigingizga yuborildi. U ham tasdiqlagach, aloqa uziladi.",
        "ru": "⏳ Запрос отправлен партнёру. После его подтверждения связь будет разорвана.",
        "en": "⏳ Request sent to your partner. Once they confirm, the link will be broken.",
    },
    "unlink_ask_partner": {
        "uz": "⚠️ *{name}* siz bilan aloqani uzishni so'ramoqda (ma'lumotlar o'chirilmaydi, faqat aloqa uziladi).\n\n"
              "Bunga roziimisiz?",
        "ru": "⚠️ *{name}* просит разорвать связь с вами (данные не удаляются, разрывается только связь).\n\n"
              "Вы согласны?",
        "en": "⚠️ *{name}* wants to break the link with you (data isn't deleted, only the link is broken).\n\n"
              "Do you agree?",
    },
    "unlink_done": {
        "uz": "🔄 Aloqa uzildi. Endi yangi sherik bilan bog'lanishingiz mumkin:",
        "ru": "🔄 Связь разорвана. Теперь вы можете связаться с новым партнёром:",
        "en": "🔄 Link broken. You can now connect with a new partner:",
    },
    "unlink_approved_notice": {
        "uz": "✅ Sherigingiz rozi bo'ldi. Aloqa uzildi. Endi yangi sherik bilan bog'lanishingiz mumkin:",
        "ru": "✅ Партнёр согласился. Связь разорвана. Теперь можно связаться с новым партнёром:",
        "en": "✅ Your partner agreed. Link broken. You can now connect with a new partner:",
    },
    "unlink_cancelled": {
        "uz": "Bekor qilindi — aloqa uzilmadi.",
        "ru": "Отменено — связь не разорвана.",
        "en": "Cancelled — the link was not broken.",
    },
    "unlink_denied_notice": {
        "uz": "❌ Sherigingiz aloqani uzishga rozi bo'lmadi.",
        "ru": "❌ Партнёр не согласился разорвать связь.",
        "en": "❌ Your partner did not agree to break the link.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    entry = T.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return text.format(**kwargs) if kwargs else text
