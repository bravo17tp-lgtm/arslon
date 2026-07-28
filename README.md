# Sevgi — Telegram Mini App 💞

Ko'p foydalanuvchili (multi-user): istalgan Telegram foydalanuvchisi kirib, taklif kodi orqali sherigi bilan bog'lanadi. Har bir juftlikning ma'lumotlari (xotiralar, kayfiyat, rejalar, sevgi xatlari, maxsus kunlar) bir-biridan to'liq ajratilgan. Ma'lumotlar PostgreSQL'da (Supabase), media fayllar Supabase Storage'da — Render qayta deploy qilinsa ham hech narsa yo'qolmaydi.

## Loyiha tuzilishi

```
love-app/
├── app/
│   ├── main.py          # FastAPI backend (API + statik frontend + bot birga ishlaydi)
│   ├── db.py             # PostgreSQL (Supabase) yordamchi funksiyalar
│   ├── storage.py         # Supabase Storage'ga media yuklash
│   ├── auth.py            # Telegram initData tekshiruvi
│   ├── telegram_bot.py    # Bot handlerlar (pairing, admin panel)
│   ├── content.py         # Savollar, iqtiboslar, sevgi tili testi savollari
│   └── static/
│       └── index.html    # Mini App interfeysi (HTML/CSS/JS)
├── requirements.txt
├── render.yaml
└── .gitignore
```

## 1-qadam: Bot yaratish

1. [@BotFather](https://t.me/BotFather) → `/newbot` → nom bering → **token** oling.
2. [@userinfobot](https://t.me/userinfobot) orqali o'z Telegram **ID**ingizni bilib oling.

## 2-qadam: Supabase (baza + media xotira) sozlash

1. [supabase.com](https://supabase.com) → bepul account → **New Project** yarating.
2. **Project Settings → Database → Connection string (URI)** dan `DATABASE_URL` oling.
3. **Project Settings → General** dan `Project URL`ni oling (`SUPABASE_URL`, `https://xxxxx.supabase.co`).
4. **Project Settings → API Keys** dan **Secret key**ni oling (`SUPABASE_SERVICE_KEY`).
5. **Storage** bo'limida `media` nomli **public** bucket yarating.

## 3-qadam: GitHub'ga yuklash

```bash
cd love-app
git init
git add .
git commit -m "Sevgi mini app"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/sevgi-app.git
git push -u origin main
```
(GitHub'da avval bo'sh repository yarating: github.com/new)

## 4-qadam: Render'da joylashtirish

1. [render.com](https://render.com) ga GitHub orqali bepul ro'yxatdan o'ting (karta shart emas).
2. **New +** → **Web Service** → GitHub repongizni tanlang.
3. Sozlamalar avtomatik `render.yaml` orqali o'qiladi. Agar qo'lda kiritish so'ralsa:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** bo'limida qo'shing:
   - `BOT_TOKEN` — BotFather'dan olgan tokeningiz
   - `ADMIN_ID` — sizning Telegram ID'ingiz (avtomatik bosh admin bo'lasiz)
   - `APP_URL` — **hozircha bo'sh qoldiring**, keyingi qadamda to'ldiramiz
   - `DATABASE_URL` — Supabase connection string
   - `SUPABASE_URL` — Supabase Project URL
   - `SUPABASE_SERVICE_KEY` — Supabase Secret key
5. **Create Web Service** bosing. Birinchi deploy 2-3 daqiqa vaqt oladi.

## 5-qadam: APP_URL ni to'ldirish

1. Deploy tugagach, Render sizga manzil beradi, masalan: `https://sevgi-mini-app.onrender.com`
2. Shu manzilni nusxalab, Render dashboard → **Environment** → `APP_URL` qiymatiga qo'ying.
3. Saqlang — Render avtomatik qayta ishga tushiradi (redeploy).

## 6-qadam: Botni sinash va sherigingizni bog'lash

1. Telegram'da botingizni toping, `/start` bosing.
2. "💌 Yangi juftlik yaratish" tugmasini bosing — sizga taklif kodi beriladi.
3. Bu kodni sherigingizga yuboring. U bot bilan `/start` qilib, "🔑 Taklif kodini kiritish"ni bosib, kodni yuborishi bilan siz bog'lanasiz.
4. Endi ikkalangiz ham "💞 Ochish" tugmasi orqali Mini App'ga kira olasiz.

Xohlagan boshqa Telegram foydalanuvchisi ham botga kirib, o'z alohida juftligini yaratishi mumkin — ularning ma'lumotlari sizniki bilan aralashmaydi.

## ⚠️ Muhim eslatmalar

**Bepul tarifning bitta cheklovi bor:**

- **Uyquga ketish** — Render'ning bepul web-service tarifida 15 daqiqa faollik bo'lmasa, server uxlaydi. Keyingi ochilishda 30-60 soniya kutish kerak bo'ladi. Ma'lumot yo'qolmaydi, faqat server "uyg'onishi" kerak.
- Ma'lumotlar bazasi va media fayllar endi Supabase'da (PostgreSQL + Storage) saqlanadi — Render qayta deploy qilinganda, server yangilanganda ham hech narsa yo'qolmaydi. Supabase bepul tarifi 500MB baza + 1GB fayl xotirasini beradi; 7 kun faollik bo'lmasa loyiha "uxlab qoladi" (Supabase dashboard'da bir marta kirib uyg'otish kifoya).

## Funksiyalar

- 🏡 **Bosh sahifa** — soniyama-soniya yangilanuvchi "birga o'tkazilgan vaqt" (yil/oy/kun/soat/daqiqa/soniya), bugungi kayfiyat, kun savoli, yaqinlashayotgan maxsus kun
- 📔 **Kundalik** — matn va rasm bilan umumiy xotiralar lentasi
- 😊 **Kayfiyat** — emoji tanlash + so'nggi 30 kunlik solishtiruvchi grafik (Chart.js)
- 📝 **Rejalar** — date-idea/vazifalar ro'yxati, bajarilganda belgilash
- 💌 **Sevgi burchagi** — bir tugma bilan sherigingizga xabar yuborish, umumiy statistika
- ⚙️ **Sozlamalar** — sevgi sanasi, maxsus kunlar, sevgi tili testi, **tema tanlash**
- 🎨 **3 xil tema** — Tungi, Bahor, Quyosh (har bir foydalanuvchi o'zinikini tanlaydi, mustaqil saqlanadi)
- ⏰ **Kunlik eslatma** — har kuni soat 21:00da (Toshkent vaqti), agar kayfiyat belgilanmagan bo'lsa, bot avtomatik eslatadi
- 📊 **Haftalik xulosa** — har yakshanba soat 21:00da, o'sha hafta haqida qisqacha statistika (xotiralar, bajarilgan rejalar, umumiy kayfiyat) avtomatik yuboriladi

### Vaqtni o'zgartirish

Eslatma va xulosa vaqti `app/main.py` faylida, `startup()` funksiyasi ichida belgilangan (`dtime(21, 0, ...)`). Boshqa vaqt kerak bo'lsa, shu qatorlarni o'zgartirib qayta yuklashingiz kifoya. Vaqt zonasi — `Asia/Tashkent` (UTC+5), kerak bo'lsa `TASHKENT = ZoneInfo("Asia/Tashkent")` qatorini o'zgartiring.

## Lokal test qilish (ixtiyoriy)

Agar Render'ga yuklashdan oldin kompyuteringizda sinab ko'rmoqchi bo'lsangiz:

```bash
cd love-app
pip install -r requirements.txt
export BOT_TOKEN="tokeningiz"
export ADMIN_ID="idingiz"
export APP_URL="https://placeholder.ngrok.io"   # mini app ochish uchun HTTPS manzil kerak
export DATABASE_URL="postgresql://..."
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_KEY="sb_secret_..."
uvicorn app.main:app --reload
```

Mini App'ni chinakam sinash uchun HTTPS manzil shart (Telegram http:// bilan ishlamaydi) — shuning uchun to'liq test faqat Render'ga yuklagandan keyin mumkin, yoki [ngrok](https://ngrok.com) kabi vosita bilan lokal serverni vaqtincha HTTPS orqali ochish mumkin.
