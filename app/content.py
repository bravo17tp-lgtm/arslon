"""Statik kontent: savollar, iqtiboslar, sevgi tili testi."""

MOOD_OPTIONS = [
    {"key": "zor", "emoji": "🥰", "label": "Zo'r", "score": 7,
     "title": "Ajoyib! 🥰", "message": "Bugun juda yaxshi kayfiyatdasiz! Shu quvonch doim siz bilan bo'lsin."},
    {"key": "yaxshi", "emoji": "😄", "label": "Yaxshi", "score": 6,
     "title": "Zo'r! 😊", "message": "Kayfiyatingiz yaxshi — buni his qilish ajoyib."},
    {"key": "oddiy", "emoji": "😐", "label": "Oddiy", "score": 5,
     "title": "Sokin kun 😐", "message": "Har kun ajoyib bo'lishi shart emas — bugun ham o'z o'rnida."},
    {"key": "charchagan", "emoji": "🥱", "label": "Charchagan", "score": 4,
     "title": "Charchagansiz 🥱", "message": "Biroz dam oling — sherigingiz sizni tushunadi."},
    {"key": "yomon", "emoji": "😔", "label": "Yomon", "score": 3,
     "title": "Yaxshi emas ekan 😔", "message": "Ertaga yaxshiroq bo'ladi. Sherigingiz sizni yoniga chorlaydi."},
    {"key": "juda_yomon", "emoji": "😢", "label": "Juda yomon", "score": 2,
     "title": "Qiyin kun ekan 😢", "message": "Yolg'iz emassiz — sherigingiz doim yoningizda."},
    {"key": "jahlim_chiqdi", "emoji": "😡", "label": "Jahlim chiqdi", "score": 1,
     "title": "Asabiylashdingiz 😡", "message": "Chuqur nafas oling — bu ham o'tib ketadi."},
]
MOOD_EMOJIS = [m["emoji"] for m in MOOD_OPTIONS]
MOOD_SCORE = {m["emoji"]: m["score"] for m in MOOD_OPTIONS}
MOOD_LABEL = {m["emoji"]: m["label"] for m in MOOD_OPTIONS}
MOOD_BY_EMOJI = {m["emoji"]: m for m in MOOD_OPTIONS}

THEMES = {
    "tungi": {
        "label": "Tungi", "swatch": "#0f1c2e",
        "bg": "#0f1c2e", "bg2": "#16273d", "bg3": "#1c3149",
        "cream": "#f3ead9", "cream-dim": "#a9a091", "cream-faint": "#6f6a5f",
        "gold": "#d4af6a", "gold-soft": "rgba(212,175,106,0.16)", "gold-dim": "#9c7e46",
        "coral": "#e0958c", "coral-soft": "rgba(224,149,140,0.16)",
        "line": "rgba(243,234,217,0.09)", "line-strong": "rgba(243,234,217,0.18)",
    },
    "bahor": {
        "label": "Bahor", "swatch": "#9bc27c",
        "bg": "#122016", "bg2": "#1a2f20", "bg3": "#203a28",
        "cream": "#eef2e6", "cream-dim": "#a8b39c", "cream-faint": "#6d7863",
        "gold": "#9bc27c", "gold-soft": "rgba(155,194,124,0.16)", "gold-dim": "#6f8f57",
        "coral": "#e8a3b8", "coral-soft": "rgba(232,163,184,0.16)",
        "line": "rgba(238,242,230,0.09)", "line-strong": "rgba(238,242,230,0.18)",
    },
    "quyosh": {
        "label": "Quyosh", "swatch": "#e8a33d",
        "bg": "#241a12", "bg2": "#33261a", "bg3": "#3f2f20",
        "cream": "#fbeee0", "cream-dim": "#c7ab8f", "cream-faint": "#8a7461",
        "gold": "#e8a33d", "gold-soft": "rgba(232,163,61,0.18)", "gold-dim": "#b8792a",
        "coral": "#e2735a", "coral-soft": "rgba(226,115,90,0.16)",
        "line": "rgba(251,238,224,0.09)", "line-strong": "rgba(251,238,224,0.18)",
    },
    "yorugor": {
        "label": "Yorug'", "swatch": "#f6ede0",
        "bg": "#faf6ef", "bg2": "#ffffff", "bg3": "#f1e8d9",
        "cream": "#3a3226", "cream-dim": "#7a6f5c", "cream-faint": "#a89d89",
        "gold": "#b8863f", "gold-soft": "rgba(184,134,63,0.14)", "gold-dim": "#8f6a30",
        "coral": "#c96a5c", "coral-soft": "rgba(201,106,92,0.14)",
        "line": "rgba(58,50,38,0.08)", "line-strong": "rgba(58,50,38,0.16)",
    },
}

QUESTIONS = [
    "Bugun eng ko'p kulgan lahzangiz qaysi edi?",
    "Hozir eng ko'p sog'ingan narsangiz nima?",
    "Agar hoziroq birga bo'lsangiz, nima qilardingiz?",
    "Sizni menda eng ko'p kuldiradigan narsa nima?",
    "Kelajakda birga qilishni orzu qilgan bitta ish?",
    "Bugun o'zingizni qanday his qildingiz — nega?",
    "Men haqimda sizni eng ko'p tinchlantiradigan narsa nima?",
    "Sevimli xotiramiz — birinchi xayolingizga kelgani?",
    "Hozir sizga eng kerakli narsa nima — quvvat, gap, quchoq?",
    "Meni kim ekanligimni bitta so'z bilan aytsangiz?",
    "Bugungi kuningizdagi eng qiyin lahza?",
    "Nimadan minnatdorsiz bugun?",
    "Men haqimda hali aytmagan bir narsangiz bormi?",
    "Eng yoqimli xotiramiz sabab nima edi?",
]

QUOTES = [
    "Masofa vaqtni cho'zadi, lekin sevgini kamaytirmaydi.",
    "Har kuni sizni tanlayman — bu odat emas, bu qaror.",
    "Sog'inch — bu ikki yurak bir xil narsani his qilayotganining isboti.",
    "Yiroqlik faqat tanani ajratadi, xayolni emas.",
    "Sizsiz o'tgan kun ham, siz haqingizdagi kun edi.",
    "Sevgi shoshilmaydi — u sabr bilan kuchayadi.",
    "Har bir 'sog'indim' — yurakdan yozilgan kichik xat.",
    "Biz orasidagi masofani faqat vaqt o'lchay oladi, hislarimiz emas.",
    "Eng qiyin kunlarda ham, sen fikrimda eng yorug' joydasan.",
    "Sevgi — bu kutish, lekin umidsizlanmaslik san'ati.",
]

LOVE_LANGUAGES = {
    "words": "So'zlar orqali izhor",
    "time": "Sifatli vaqt",
    "gifts": "Sovg'alar",
    "acts": "Yordam ishlari",
    "touch": "Jismoniy yaqinlik",
}

LOVE_TEST_QUESTIONS = [
    {
        "q": "Sizni eng ko'p nima xursand qiladi?",
        "options": [
            {"key": "words", "text": "\"Seni yaxshi ko'raman\" degan so'zlarni eshitish"},
            {"key": "time", "text": "Birga, telefonlarsiz vaqt o'tkazish"},
            {"key": "gifts", "text": "Kichik bo'lsa ham, kutilmagan sovg'a"},
            {"key": "acts", "text": "U siz uchun biror ishni bajarib qo'yishi"},
            {"key": "touch", "text": "Quchoqlash, qo'l ushlash"},
        ],
    },
    {
        "q": "Xafa bo'lganingizda nima eng yaxshi yordam beradi?",
        "options": [
            {"key": "words", "text": "Mehribon so'zlar bilan tinchlantirish"},
            {"key": "time", "text": "Yoningizda jim o'tirish"},
            {"key": "gifts", "text": "Sevimli narsangizni sovg'a qilish"},
            {"key": "acts", "text": "Sizning o'rningizga biror ishni qilib qo'yish"},
            {"key": "touch", "text": "Qattiq quchoqlash"},
        ],
    },
    {
        "q": "Sherigingizga g'amxo'rlik qanday ko'rsatasiz?",
        "options": [
            {"key": "words", "text": "Unga ko'p iliq so'zlar aytaman"},
            {"key": "time", "text": "Vaqtimni to'liq unga bag'ishlayman"},
            {"key": "gifts", "text": "Kichik sovg'alar tayyorlayman"},
            {"key": "acts", "text": "Unga yordam beraman, ishlarini yengillashtiraman"},
            {"key": "touch", "text": "Yaqin turishga, teginishga harakat qilaman"},
        ],
    },
    {
        "q": "Idealda kechqurun qanday o'tsin deysiz?",
        "options": [
            {"key": "words", "text": "Uzoq, chin dildan suhbat"},
            {"key": "time", "text": "Birga film ko'rish, hech nima qilmasdan yonma-yon"},
            {"key": "gifts", "text": "Bir-birimizga kichik sovg'a tayyorlaymiz"},
            {"key": "acts", "text": "Birga ovqat tayyorlaymiz"},
            {"key": "touch", "text": "Quchoqlashib, yaqin o'tiramiz"},
        ],
    },
    {
        "q": "Nima sizni eng ko'p ranjitadi?",
        "options": [
            {"key": "words", "text": "Qo'pol yoki loqayd gaplar"},
            {"key": "time", "text": "Diqqatsizlik, doim band bo'lish"},
            {"key": "gifts", "text": "Muhim kunni unutish"},
            {"key": "acts", "text": "Yordam so'raganda e'tiborsizlik"},
            {"key": "touch", "text": "Jismoniy yiroqlik, sovuqlik"},
        ],
    },
]
