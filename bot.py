import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG FROM ENV ================= #

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ================= PYROGRAM APP ================= #

app = Client(
    "tmdb_movie_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= TEMP USER STORAGE ================= #

user_data = {}

# ================= TMDB FETCH ================= #

def fetch_tmdb(movie_name):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_name,
        "language": "en-US"
    }

    res = requests.get(search_url, params=params).json()
    if not res.get("results"):
        return None

    movie = res["results"][0]

    genre_url = "https://api.themoviedb.org/3/genre/movie/list"
    genre_res = requests.get(
        genre_url,
        params={"api_key": TMDB_API_KEY}
    ).json()

    genre_map = {g["id"]: g["name"] for g in genre_res["genres"]}
    genres = [genre_map.get(i) for i in movie.get("genre_ids", []) if i in genre_map]

    poster = None
    if movie.get("poster_path"):
        poster = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]

    return {
        "title": movie["title"],
        "year": movie["release_date"][:4] if movie.get("release_date") else "N/A",
        "rating": round(movie["vote_average"], 1),
        "genres": genres,
        "poster": poster
    }

# ================= ADMIN FLOW ================= #

@app.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_handler(client, message):
    uid = message.from_user.id

    if uid not in user_data:
        user_data[uid] = {"step": "movie"}

    step = user_data[uid]["step"]

    # STEP 1: MOVIE NAME
    if step == "movie":
        user_data[uid]["movie_name"] = message.text
        user_data[uid]["step"] = "link"
        await message.reply("🔗 Download link ?")
        return

    # STEP 2: DOWNLOAD LINK
    if step == "link":
        user_data[uid]["link"] = message.text
        user_data[uid]["step"] = "send_where"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Send to Channel", callback_data="channel")],
            [InlineKeyboardButton("👤 Send to Private", callback_data="private")]
        ])

        await message.reply(
            "Want to send directly to the channel ?",
            reply_markup=buttons
        )

# ================= CALLBACK ================= #

@app.on_callback_query(filters.user(ADMIN_ID))
async def callback_handler(client, callback):
    uid = callback.from_user.id
    data = user_data.get(uid)

    movie = fetch_tmdb(data["movie_name"])
    if not movie:
        await callback.message.edit("❌ Movie not found")
        return

    caption = f"""
🎬 {movie['title']} {movie['year']}
━━━━━━━━━━━━━━━━━━
➥ Rating : ★ {movie['rating']}/10
➥ Genres : {', '.join(movie['genres'])}
➥ Languages : Tamil
➥ Qualities : 480p, 720p, WEB-DL
"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Now 📥", url=data["link"])]
    ])

    chat_id = CHANNEL_ID if callback.data == "channel" else uid

    await client.send_photo(
        chat_id=chat_id,
        photo=movie["poster"],
        caption=caption,
        reply_markup=buttons
    )

    await callback.message.edit("✅ Posted successfully")
    user_data.pop(uid, None)

# ================= RUN ================= #

app.run()
