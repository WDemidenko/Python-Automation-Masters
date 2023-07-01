import os
import time
import requests
import telebot
import urllib.request

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)


def wait_for_chat_id() -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    while True:
        response = requests.get(url)
        data = response.json()
        if "result" in data and data["result"]:
            chat_id = data["result"][-1]["message"]["chat"]["id"]
            with open(".env", "a") as env_file:
                env_file.write(f"\nCHAT_ID={chat_id}")
            break
        else:
            print("Waiting for chat ID")
            time.sleep(1)


def send_notification(ad_id: int, message: str = "") -> None:
    from main import create_connection

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, url, price, bidfax_link FROM ads WHERE id_auto=?",
            (ad_id,),
        )
        name, url, price, bidfax_link = cursor.fetchone()
        cursor.execute("SELECT photo_link FROM photos WHERE ad_id=?", (ad_id,))
        photo_links = cursor.fetchall()

    full_message = (
        f"{message}\n"
        f"<a href='{url}'>{name}</a>\n"
        f"Price: {price}$\n"
        f"<a href='{bidfax_link}'>bidfax</a>"
    )

    # Download and add each photo to the media list
    media = []

    for index, link in enumerate(photo_links):
        file_name = link[0].split("/")[-1]
        urllib.request.urlretrieve(link[0], file_name)

        with open(file_name, "rb") as file:
            media.append(
                telebot.types.InputMediaPhoto(
                    file.read(),
                    caption=full_message if index == 0 else "",
                    parse_mode="HTML",
                )
            )

    if media:
        chat_id = os.getenv("CHAT_ID")
        bot.send_media_group(chat_id=chat_id, media=media)

    # Delete the downloaded photos
    for link in photo_links:
        file_name = link[0].split("/")[-1]
        if os.path.exists(file_name):
            os.remove(file_name)
