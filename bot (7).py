import html
import sqlite3
from telebot import TeleBot, types

BOT_TOKEN = "8810853087:AAHGp-BfME4uNEIXgfwQqpbzZ-fQabpkfbA"  # Tokeningiz
ADMIN_ID = 7401059544  # Telegram ID
CHANNEL_ID = "@AniClipz_anime"  # Kanal username'i

bot = TeleBot(BOT_TOKEN)

user_states = {}


# --- BAZANI SOZLASH ---
def init_db():
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime (
            code TEXT PRIMARY KEY,
            title TEXT,
            qism TEXT,
            janr TEXT,
            tili TEXT,
            photo TEXT,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            anime_code TEXT,
            ep_num INTEGER,
            file_id TEXT,
            PRIMARY KEY (anime_code, ep_num)
        )
    """)
  conn.commit()
  conn.close()


init_db()


# --- BOSH MENYU TUGMALARI ---
def main_menu():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  btn_search = types.KeyboardButton("🔍 Anime qidirish")
  btn_guide = types.KeyboardButton("ℹ️ Qo'llanma")
  markup.add(btn_search, btn_guide)
  return markup


# --- QIDIRUV TURLARI MENYUSI ---
def search_type_menu():
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "🏷 Anime nomi orqali", callback_data="search_name"
      ),
      types.InlineKeyboardButton(
          "⏱ So'ngi yuklanganlar", callback_data="search_latest"
      ),
  )
  markup.add(
      types.InlineKeyboardButton(
          "💬 Janr orqali qidirish", callback_data="search_genre"
      )
  )
  markup.add(
      types.InlineKeyboardButton("📌 Kod orqali", callback_data="search_code")
  )
  markup.add(
      types.InlineKeyboardButton(
          "📚 Barcha animelar", callback_data="search_all"
      )
  )
  return markup


# --- OBUNANI TEKSHIRISH ---
def check_sub(user_id):
  try:
    member = bot.get_chat_member(CHANNEL_ID, user_id)
    if member.status in ["creator", "administrator", "member"]:
      return True
    return False
  except Exception:
    return False


# --- START VA DEEPLINK ---
@bot.message_handler(commands=["start"])
def start_handler(message):
  args = message.text.split()
  user_id = message.from_user.id

  if len(args) > 1:
    anime_code = args[1]

    if not check_sub(user_id):
      markup = types.InlineKeyboardMarkup()
      btn_channel = types.InlineKeyboardButton(
          "📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"
      )
      btn_check = types.InlineKeyboardButton(
          "✅ A'zo bo'ldim", callback_data=f"check_{anime_code}"
      )
      markup.add(btn_channel, btn_check)

      bot.send_message(
          message.chat.id,
          "⚠️ <b>Animeni tomosha qilish uchun avval kanalimizga obuna bo'ling!</b>\n\nObuna bo'lgach, 'A'zo bo'ldim' tugmasini bosing:",
          parse_mode="HTML",
          reply_markup=markup,
      )
      return

    send_anime_info(message.chat.id, anime_code)
  else:
    bot.send_message(
        message.chat.id,
        "👋 Xush kelibsiz! Anime kodini yuboring yoki menyudan foydalaning.",
        reply_markup=main_menu(),
    )


# --- CHECK CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_callback(call):
  anime_code = call.data.split("_")[1]
  user_id = call.from_user.id

  if check_sub(user_id):
    bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_anime_info(call.message.chat.id, anime_code)
  else:
    bot.answer_callback_query(
        call.id, "❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True
    )


# --- MENYU TUGMALARI ---
@bot.message_handler(
    func=lambda msg: msg.text in ["🔍 Anime qidirish", "ℹ️ Qo'llanma"]
)
def menu_buttons(message):
  if message.text == "🔍 Anime qidirish":
    bot.send_message(
        message.chat.id,
        "🔍 Qidiruv tipini tanlang:",
        reply_markup=search_type_menu(),
    )
  elif message.text == "ℹ️ Qo'llanma":
    bot.send_message(
        message.chat.id,
        f"🤖 Ushbu bot orqali {CHANNEL_ID} kanalidagi animelarni tomosha qilishingiz mumkin.\n\nKanalimizdagi postlar ostidagi '🍿 Tomosha qilish' tugmasini bosing yoki anime kodini botga yuboring!",
    )


# --- QIDIRUV TURLARI CALLBACKLARI ---
@bot.callback_query_handler(func=lambda call: call.data == "search_name")
def search_name_cb(call):
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, "🏷 Qidirilayotgan anime nomini yuboring:")


@bot.callback_query_handler(func=lambda call: call.data == "search_code")
def search_code_cb(call):
  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id, "📌 Tomosha qilmoqchi bo'lgan anime kodini yuboring:"
  )


@bot.callback_query_handler(func=lambda call: call.data == "search_latest")
def search_latest_cb(call):
  bot.answer_callback_query(call.id)
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT code, title, qism FROM anime ORDER BY created_at DESC LIMIT 5"
  )
  animes = cursor.fetchall()
  conn.close()

  if animes:
    text = "⏱ <b>So'ngi qo'shilgan animelar:</b>\n\n"
    for a in animes:
      text += f"🎬 {a[1]} ({a[2]}) - Kod: <code>{a[0]}</code>\n"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")
  else:
    bot.send_message(call.message.chat.id, "❌ Hozircha animelar yo'q.")


@bot.callback_query_handler(func=lambda call: call.data == "search_genre")
def search_genre_cb(call):
  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id, "💬 Janr nomini yuboring (masalan: #jangari):"
  )


@bot.callback_query_handler(func=lambda call: call.data == "search_all")
def search_all_cb(call):
  bot.answer_callback_query(call.id)
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT code, title FROM anime ORDER BY title ASC LIMIT 20")
  animes = cursor.fetchall()
  conn.close()

  if animes:
    text = "📚 <b>Barcha animelar (Top 20):</b>\n\n"
    for a in animes:
      text += f"▪️ {a[1]} - Kod: <code>{a[0]}</code>\n"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")
  else:
    bot.send_message(call.message.chat.id, "❌ Hozircha animelar bazada yo'q.")


# --- QISMLAR KLAVIATURASI (SAHIFALASH / PAGINATION BILAN) ---
def get_episodes_keyboard(anime_code, episodes, page=0):
  markup = types.InlineKeyboardMarkup(row_width=4)
  per_page = 12
  total_episodes = len(episodes)

  start_idx = page * per_page
  end_idx = min(start_idx + per_page, total_episodes)

  page_episodes = episodes[start_idx:end_idx]

  buttons = []
  for ep in page_episodes:
    ep_num = ep[0]
    btn = types.InlineKeyboardButton(
        f"{ep_num}", callback_data=f"getep_{anime_code}_{ep_num}"
    )
    buttons.append(btn)

  if buttons:
    markup.add(*buttons)

  nav_buttons = []
  if page > 0:
    nav_buttons.append(
        types.InlineKeyboardButton(
            "⬅️ Orqaga", callback_data=f"page_{anime_code}_{page-1}"
        )
    )
  if end_idx < total_episodes:
    nav_buttons.append(
        types.InlineKeyboardButton(
            "Oldinga ➡️", callback_data=f"page_{anime_code}_{page+1}"
        )
    )

  if nav_buttons:
    markup.row(*nav_buttons)

  return markup


# --- ANIME HAQIDA MA'LUMOT ---
def send_anime_info(chat_id, anime_code):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()

  cursor.execute(
      "SELECT title, qism, janr, tili, photo, views FROM anime WHERE code = ?",
      (anime_code,),
  )
  anime = cursor.fetchone()

  if not anime:
    bot.send_message(chat_id, "❌ Afsuski, bu kod bo'yicha anime topilmadi.")
    conn.close()
    return

  new_views = (anime[5] or 0) + 1
  cursor.execute(
      "UPDATE anime SET views = ? WHERE code = ?", (new_views, anime_code)
  )

  cursor.execute(
      "SELECT ep_num FROM episodes WHERE anime_code = ? ORDER BY ep_num ASC",
      (anime_code,),
  )
  episodes = cursor.fetchall()
  conn.commit()
  conn.close()

  bot_info = bot.get_me()
  caption = (
      f"🎬 <b>| {html.escape(str(anime[0]))}</b>\n"
      f"----------------------\n"
      f"📌 <b>Qismi:</b> {html.escape(str(anime[1]))}\n"
      f"🎭 <b>Janri:</b> {html.escape(str(anime[2]))}\n"
      f"🌐 <b>Tili:</b> {html.escape(str(anime[3]))}\n\n"
      f"👁 <b>Ko'rishlar soni:</b> {new_views}\n"
      f"🔑 <b>KODI:</b> « {html.escape(str(anime_code))} »\n\n"
      f"🤖 <b>BOT – @{bot_info.username}</b>"
  )

  markup = get_episodes_keyboard(anime_code, episodes, page=0)

  bot.send_photo(
      chat_id, anime[4], caption=caption, parse_mode="HTML", reply_markup=markup
  )


# --- SAHIFALASH (PAGINATION) CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def handle_pagination(call):
  _, anime_code, page_str = call.data.split("_")
  page = int(page_str)

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT ep_num FROM episodes WHERE anime_code = ? ORDER BY ep_num ASC",
      (anime_code,),
  )
  episodes = cursor.fetchall()
  conn.close()

  markup = get_episodes_keyboard(anime_code, episodes, page=page)

  try:
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )
  except Exception:
    pass
  bot.answer_callback_query(call.id)


# --- QISM TUGMASI ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("getep_"))
def send_episode_video(call):
  _, anime_code, ep_num = call.data.split("_")

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()

  cursor.execute("SELECT title FROM anime WHERE code = ?", (anime_code,))
  anime = cursor.fetchone()

  cursor.execute(
      "SELECT file_id FROM episodes WHERE anime_code = ? AND ep_num = ?",
      (anime_code, ep_num),
  )
  episode = cursor.fetchone()
  conn.close()

  if episode and episode[0]:
    bot.answer_callback_query(call.id, f"🎬 {ep_num}-qism yuklanmoqda...")
    caption = f"🎬 <b>{html.escape(anime[0])}</b>\n\n🔘 <b>{ep_num}-qism</b>"
    bot.send_video(
        call.message.chat.id,
        episode[0],
        caption=caption,
        parse_mode="HTML",
    )
  else:
    bot.answer_callback_query(
        call.id, "❌ Bu qism topilmadi!", show_alert=True
    )


# --- ADMIN: /add (YANGI ANIME QO'SHISH) ---
@bot.message_handler(commands=["add"])
def add_anime_start(message):
  if message.from_user.id != ADMIN_ID:
    return
  user_states[message.chat.id] = {"step": "code", "videos": []}
  bot.send_message(message.chat.id, "1️⃣ Anime KODINI kiriting (masalan: 122):")


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "code"
)
def get_code(message):
  user_states[message.chat.id]["code"] = message.text.strip()
  user_states[message.chat.id]["step"] = "title"
  bot.send_message(
      message.chat.id, "2️⃣ Anime NOMINI kiriting (masalan: Senga intilib):"
  )


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "title"
)
def get_title(message):
  user_states[message.chat.id]["title"] = message.text.strip()
  user_states[message.chat.id]["step"] = "qism"
  bot.send_message(message.chat.id, "3️⃣ QISMINI kiriting (masalan: 1-41):")


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "qism"
)
def get_qism(message):
  user_states[message.chat.id]["qism"] = message.text.strip()
  user_states[message.chat.id]["step"] = "janr"
  bot.send_message(
      message.chat.id, "4️⃣ JANRINI kiriting (masalan: Romantika, Drama):"
  )


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "janr"
)
def get_janr(message):
  user_states[message.chat.id]["janr"] = message.text.strip()
  user_states[message.chat.id]["step"] = "tili"
  bot.send_message(message.chat.id, "5️⃣ Anime TILINI kiriting (masalan: O'zbek):")


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "tili"
)
def get_tili(message):
  user_states[message.chat.id]["tili"] = message.text.strip()
  user_states[message.chat.id]["step"] = "photo"
  bot.send_message(message.chat.id, "6️⃣ Endi anime POSTERINI yuboring:")


@bot.message_handler(
    content_types=["photo"],
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "photo",
)
def get_photo(message):
  user_states[message.chat.id]["photo"] = message.photo[-1].file_id
  user_states[message.chat.id]["step"] = "videos"

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add("✅ Tugatish va Kanalga joylash")

  bot.send_message(
      message.chat.id,
      "📥 Endi anime qismlarini yuboring va tugatgach tugmani bosing.",
      reply_markup=markup,
  )


@bot.message_handler(
    content_types=["video"],
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "videos",
)
def get_videos(message):
  video_id = message.video.file_id
  user_states[message.chat.id]["videos"].append(video_id)
  ep_count = len(user_states[message.chat.id]["videos"])
  bot.send_message(message.chat.id, f"➕ {ep_count}-qism qabul qilindi!")


@bot.message_handler(
    func=lambda msg: msg.text == "✅ Tugatish va Kanalga joylash"
    and user_states.get(msg.chat.id, {}).get("step") == "videos"
)
def finish_add(message):
  data = user_states.pop(message.chat.id, {})
  code = data.get("code")
  title = data.get("title")
  qism = data.get("qism")
  janr = data.get("janr")
  tili = data.get("tili")
  photo_id = data.get("photo")
  videos = data.get("videos", [])

  if not videos:
    bot.send_message(message.chat.id, "⚠️ Video yuborilmadi!")
    user_states[message.chat.id] = data
    return

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()

  # Anime ma'lumotlarini saqlash
  cursor.execute(
      """
        INSERT OR REPLACE INTO anime (code, title, qism, janr, tili, photo)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
      (code, title, qism, janr, tili, photo_id),
  )

  # Qismlarni xavfsiz qo'shish (eskilari o'chib ketmaydi, mavjud bo'lsa yangilanadi, yangi bo'lsa qo'shiladi)
  for idx, vid in enumerate(videos, 1):
    cursor.execute(
        """
            INSERT OR REPLACE INTO episodes (anime_code, ep_num, file_id)
            VALUES (?, ?, ?)
        """,
        (code, idx, vid),
    )

  conn.commit()
  conn.close()

  caption = (
      f"🎬 <b>{html.escape(str(title))}</b>\n\n"
      f"🔑 <b>Kodi:</b> <code>{html.escape(str(code))}</code>\n"
      f"📌 <b>Qismi:</b> {html.escape(str(qism))}\n"
      f"🎭 <b>Janri:</b> {html.escape(str(janr))}\n"
      f"🌐 <b>Tili:</b> {html.escape(str(tili))}\n\n"
      f"🍿 <i>Tomosha qilish uchun quyidagi tugmani bosing!</i>"
  )

  bot_info = bot.get_me()
  markup = types.InlineKeyboardMarkup()
  btn_watch = types.InlineKeyboardButton(
      "🍿 Tomosha qilish", url=f"https://t.me/{bot_info.username}?start={code}"
  )
  markup.add(btn_watch)

  try:
    bot.send_photo(
        CHANNEL_ID,
        photo_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=markup,
    )
    bot.send_message(
        message.chat.id,
        f"✅ Anime va {len(videos)} ta qism saqlandi!",
        reply_markup=main_menu(),
    )
  except Exception as e:
    bot.send_message(
        message.chat.id, f"❌ Xatolik: {e}", reply_markup=main_menu()
    )


# --- ADMIN: /add_ep (MAVJUD ANIMEGA YANGI QISMLAR QO'SHISH) ---
@bot.message_handler(commands=["add_ep"])
def add_ep_start(message):
  if message.from_user.id != ADMIN_ID:
    return
  user_states[message.chat.id] = {"step": "ep_code", "videos": []}
  bot.send_message(
      message.chat.id,
      "📌 Qaysi anime kodiga qo'shimcha qism qo'shmoqchisiz? Kodni kiriting:",
  )


@bot.message_handler(
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "ep_code"
)
def get_ep_code(message):
  code = message.text.strip()
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT title FROM anime WHERE code = ?", (code,))
  anime = cursor.fetchone()
  conn.close()

  if not anime:
    bot.send_message(
        message.chat.id,
        "❌ Bunday kodli anime topilmadi! /add_ep buyrug'ini qaytadan bosing.",
    )
    user_states.pop(message.chat.id, None)
    return

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT MAX(ep_num) FROM episodes WHERE anime_code = ?", (code,)
  )
  max_ep = cursor.fetchone()[0] or 0
  conn.close()

  user_states[message.chat.id]["code"] = code
  user_states[message.chat.id]["start_ep"] = max_ep + 1
  user_states[message.chat.id]["step"] = "ep_videos"

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add("✅ Qismlarni saqlash")

  bot.send_message(
      message.chat.id,
      f"✅ Anime topildi: <b>{anime[0]}</b>\n\n"
      f"Hozirda oxirgi qism: <b>{max_ep}</b>.\n"
      f"Endi yangi qismlarni ketma-ket yuboring (keyingi qism {max_ep + 1}-dan boshlanadi). Tugatgach tugmani bosing:",
      parse_mode="HTML",
      reply_markup=markup,
  )


@bot.message_handler(
    content_types=["video"],
    func=lambda msg: user_states.get(msg.chat.id, {}).get("step")
    == "ep_videos",
)
def get_ep_videos(message):
  video_id = message.video.file_id
  user_states[message.chat.id]["videos"].append(video_id)
  total_added = len(user_states[message.chat.id]["videos"])
  start_num = user_states[message.chat.id]["start_ep"]
  current_ep = start_num + total_added - 1
  bot.send_message(
      message.chat.id, f"➕ {current_ep}-qism bo'lib qabul qilindi!"
  )


@bot.message_handler(
    func=lambda msg: msg.text == "✅ Qismlarni saqlash"
    and user_states.get(msg.chat.id, {}).get("step") == "ep_videos"
)
def finish_add_ep(message):
  data = user_states.pop(message.chat.id, {})
  code = data.get("code")
  start_ep = data.get("start_ep")
  videos = data.get("videos", [])

  if not videos:
    bot.send_message(message.chat.id, "⚠️ Video yuborilmadi!")
    user_states[message.chat.id] = data
    return

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()

  for i, vid in enumerate(videos):
    ep_num = start_ep + i
    cursor.execute(
        """
            INSERT OR REPLACE INTO episodes (anime_code, ep_num, file_id)
            VALUES (?, ?, ?)
        """,
        (code, ep_num, vid),
    )

  conn.commit()
  conn.close()

  bot.send_message(
      message.chat.id,
      f"✅ {code}-kodli animega {len(videos)} ta yangi qism qo'shildi!",
      reply_markup=main_menu(),
  )


# --- MATNNI QIDIRISH ---
@bot.message_handler(func=lambda msg: True)
def handle_text(message):
  if message.chat.id in user_states:
    return
  query = message.text.strip()

  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT code FROM anime WHERE code = ? OR title LIKE ? OR janr LIKE ?",
      (query, f"%{query}%", f"%{query}%"),
  )
  found = cursor.fetchone()
  conn.close()

  if found:
    send_anime_info(message.chat.id, found[0])
  else:
    send_anime_info(message.chat.id, query)


# --- BOTNI ISHGA TUSHIRISH (XATOLIKLARDAN HIMOYA BILAN) ---
import time

if __name__ == "__main__":
  while True:
    try:
      bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
      print(f"Xatolik yuz berdi: {e}")
      time.sleep(3)
