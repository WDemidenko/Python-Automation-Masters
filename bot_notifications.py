import os

import telebot
import urllib.request

BOT_TOKEN = "token"
CHAT_ID = "chat_id"

bot = telebot.TeleBot(BOT_TOKEN)


def send_notification(ad_id, message: str = ""):
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
        bot.send_media_group(chat_id=CHAT_ID, media=media)

    # Delete the downloaded photos
    for link in photo_links:
        file_name = link[0].split("/")[-1]
        if os.path.exists(file_name):
            os.remove(file_name)
