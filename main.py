from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

app = Client(
    "movie_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_data = {}

def fetch_tmdb(movie_name):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_name,
        "language": "en-US"
    }
    r = requests.get(url, params=params).json()
    if not r["results"]:
        return None

    m = r["results"][0]

    genres = []
    if m.get("genre_ids"):
        g_url = "https://api.themoviedb.org/3/genre/movie/list"
        g = requests.get(g_url, params={"api_key": TMDB_API_KEY}).json()
        genre_map = {x["id"]: x["name"] for x in g["genres"]}
        genres = [genre_map[i] for i in m["genre_ids"] if i in genre_map]

    return {
        "title": m["title"],
        "year": m["release_date"][:4] if m.get("release_date") else "N/A",
        "rating": round(m["vote_average"], 1),
        "genres": genres,
        "poster": "https://image.tmdb.org/t/p/w500" + m["poster_path"]
    }

@app.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_flow(client, message):
    uid = message.from_user.id

    if uid not in user_data:
        user_data[uid] = {"step": "movie"}

    step = user_data[uid]["step"]

    if step == "movie":
        user_data[uid]["movie_name"] = message.text
        user_data[uid]["step"] = "link"
        await message.reply("🔗 Download link ?")
        return

    if step == "link":
        user_data[uid]["link"] = message.text
        user_data[uid]["step"] = "send_where"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Channel", callback_data="send_channel")],
            [InlineKeyboardButton("👤 Private", callback_data="send_private")]
        ])
        await message.reply("Want to send directly to the channel ?", reply_markup=buttons)
        return

@app.on_callback_query()
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

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Now 📥", url=data["link"])]
    ])

    if callback.data == "send_channel":
        chat_id = CHANNEL_ID
    else:
        chat_id = uid

    await client.send_photo(
        chat_id=chat_id,
        photo=movie["poster"],
        caption=caption,
        reply_markup=btn
    )

    await callback.message.edit("✅ Posted successfully")
    user_data.pop(uid, None)

app.run()
