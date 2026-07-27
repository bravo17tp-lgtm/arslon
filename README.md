# Sevgi — Telegram Mini App 💞

Faqat siz va sevgilingiz uchun: kirish tasdiqlash, jonli "birga" hisoblagichi, kundalik, kayfiyat grafigi, rejalar, kun savoli, sevgi xati, sevgi tili testi va maxsus kunlar eslatmasi.

## Loyiha tuzilishi

```
love-app/
├── app/
│   ├── main.py          # FastAPI backend (API + statik frontend + bot birga ishlaydi)
│   ├── db.py             # SQLite yordamchi funksiyalar
│   ├── auth.py            # Telegram initData tekshiruvi
│   ├── telegram_bot.py    # Bot handlerlar (ro'yxatdan o'tish, tasdiqlash)
│   ├── content.py         # Savollar, iqtiboslar, sevgi tili testi savollari
│   └── static/
│       └── index.html    # Mini App interfeysi (HTML/CSS/JS, Chart.js)
├── requirements.txt
├── render.yaml
└── .gitignore
```

## 1-qadam: Bot yaratish

1. [@BotFather](https://t.me/BotFather) → `/newbot` → nom bering → **token** oling.
2. [@userinfobot](https://t.me/userinfobot) orqali o'z Telegram **ID**ingizni bilib oling.

## 2-qadam: GitHub'ga yuklash

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

## 3-qadam: Render'da joylashtirish

1. [render.com](https://render.com) ga GitHub orqali bepul ro'yxatdan o'ting (karta shart emas).
2. **New +** → **Web Service** → GitHub repongizni tanlang.
3. Sozlamalar avtomatik `render.yaml` orqali o'qiladi. Agar qo'lda kiritish so'ralsa:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** bo'limida qo'shing:
   - `BOT_TOKEN` — BotFather'dan olgan tokeningiz
   - `ADMIN_ID` — sizning Telegram ID'ingiz
   - `APP_URL` — **hozircha bo'sh qoldiring**, keyingi qadamda to'ldiramiz
5. **Create Web Service** bosing. Birinchi deploy 2-3 daqiqa vaqt oladi.

## 4-qadam: APP_URL ni to'ldirish

1. Deploy tugagach, Render sizga manzil beradi, masalan: `https://sevgi-mini-app.onrender.com`
2. Shu manzilni nusxalab, Render dashboard → **Environment** → `APP_URL` qiymatiga qo'ying.
3. Saqlang — Render avtomatik qayta ishga tushiradi (redeploy).

## 5-qadam: Botni sinash

1. Telegram'da botingizni toping, `/start` bosing.
2. Siz `ADMIN_ID` bo'lganingiz uchun avtomatik tasdiqlanasiz — "💞 Ochish" tugmasi chiqadi, bosing.
3. Mini App ochiladi.

## 6-qadam: Sevgilingizni qo'shish

1. Bot username'ini (`@sizning_botingiz`) unga yuboring.
2. U `/start` bossa, sizga (adminga) tasdiqlash so'rovi keladi — "✅ Tasdiqlash" bosing.
3. Endi u ham "💞 Ochish" orqali kira oladi.

## ⚠️ Muhim eslatmalar

**Bepul tarifning ikkita cheklovi bor:**

1. **Uyquga ketish** — 15 daqiqa faollik bo'lmasa, server uxlaydi. Keyingi ochilishda 30-60 soniya kutish kerak bo'ladi. Ma'lumot yo'qolmaydi, faqat server "uyg'onishi" kerak.

2. **Ma'lumotlar bazasi (SQLite) doimiy emas** — Render bepul tarifida fayl tizimi har safar siz kodni qayta deploy qilganingizda (yangi `git push`) tozalanadi. Ya'ni:
   - Oddiy ishlatish (kirish, kayfiyat belgilash, kundalik yozish) — ma'lumot saqlanaveradi, hech narsa yo'qolmaydi.
   - Lekin agar kelajakda kodni yangilab qayta yuklasangiz — **baza tozalanadi**, hamma yozuvlar o'chadi.
   - Bunga yechim: Render'ning **Persistent Disk** funksiyasi (oyiga ~$1 dan boshlanadi) yoki tashqi bepul baza (masalan [Turso](https://turso.tech) yoki [Supabase](https://supabase.com) bepul tarifi). Agar ma'lumotlaringiz uzoq muddat qadrli bo'lsa, buni keyinroq qo'shishni tavsiya qilaman — aytsangiz shu qismni ham sozlab beraman.

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
uvicorn app.main:app --reload
```

Mini App'ni chinakam sinash uchun HTTPS manzil shart (Telegram http:// bilan ishlamaydi) — shuning uchun to'liq test faqat Render'ga yuklagandan keyin mumkin, yoki [ngrok](https://ngrok.com) kabi vosita bilan lokal serverni vaqtincha HTTPS orqali ochish mumkin.
