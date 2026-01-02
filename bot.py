import os
import requests
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== CONFIG ==========
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

app = Client(
    "movie_scraper_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_data = {}

# ========== SCRAPE IMDb ==========
def scrape_imdb(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("h1").text.strip()
    year = soup.find("span", id="titleYear")
    year = year.text.replace("(", "").replace(")", "") if year else ""

    rating = soup.find("span", itemprop="ratingValue")
    rating = rating.text if rating else "N/A"

    genres = soup.select("div.subtext a")
    genres = [g.text for g in genres if "title" not in g.get("href", "")]

    poster = soup.find("div", class_="poster")
    poster = poster.find("img")["src"] if poster else None

    return {
        "title": title,
        "year": year,
        "rating": rating,
        "genres": genres,
        "poster": poster
    }

# ========== START ==========
@app.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start_cmd(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply(
        "🎬 Movie Scraper Bot\n\n"
        "➡️ Send movie link (IMDb)\n"
        "➡️ /cancel to reset"
    )

@app.on_message(filters.command("cancel") & filters.user(ADMIN_ID))
async def cancel_cmd(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply("❌ Cancelled. Send movie link again.")

# ========== ADMIN FLOW ==========
@app.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_flow(client, message):
    uid = message.from_user.id
    text = message.text

    if text.startswith("/"):
        return

    if uid not in user_data:
        user_data[uid] = {"step": "link"}

    step = user_data[uid]["step"]

    # STEP 1: MOVIE PAGE LINK
    if step == "link":
        if "imdb.com/title" not in text:
            await message.reply("❌ Invalid IMDb link.\nSend correct movie link.")
            return

        user_data[uid]["movie_url"] = text
        user_data[uid]["step"] = "download"
        await message.reply("🔗 Send download link")
        return

    # STEP 2: DOWNLOAD LINK
    if step == "download":
        if not text.startswith("http"):
            await message.reply("❌ Invalid download link.\nSend again.")
            return

        user_data[uid]["download"] = text
        movie = scrape_imdb(user_data[uid]["movie_url"])

        caption = f"""
🎬 {movie['title']} {movie['year']}
━━━━━━━━━━━━━━━━━━
➥ Rating : ★ {movie['rating']}/10
➥ Genres : {', '.join(movie['genres'])}
➥ Languages : Tamil
➥ Qualities : 480p, 720p, 1080p
"""

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Download Now 📥", url=user_data[uid]["download"])]
        ])

        await client.send_photo(
            chat_id=CHANNEL_ID,
            photo=movie["poster"],
            caption=caption,
            reply_markup=buttons
        )

        await message.reply("✅ Posted successfully")
        user_data.pop(uid, None)

# ========== RUN ==========
app.run()
