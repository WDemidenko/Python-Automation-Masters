import json
import re
import sqlite3
from sqlite3 import Error
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests as requests

BASE_URL = "https://auto.ria.com"
SEARCH_URL = "search/?indexName=auto&categories.main.id=1&brand.id[0]=79&model.id[0]=2104&country.import.usa.not=0&price.currency=1&abroad.not=0&custom.not=1&damage.not=0&page=0&size=1000"


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("ads_database.db")
        return conn
    except Error as e:
        print(e)

    return conn


def create_tables(conn):
    ads_table_sql = """
    CREATE TABLE IF NOT EXISTS ads (
        id_auto INTEGER PRIMARY KEY,
        name TEXT,
        url TEXT,
        price INTEGER
    )
    """
    photos_table_sql = """
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY,
        ad_id INTEGER,
        photo_link TEXT,
        FOREIGN KEY (ad_id) REFERENCES ads (id_auto)
    )
    """
    conn.execute(ads_table_sql)
    conn.execute(photos_table_sql)
    conn.commit()


def insert_ad(conn, data):
    placeholders = ", ".join(["?" for _ in data])
    fields = ", ".join(data.keys())
    values = tuple(data.values())

    sql = f"INSERT OR REPLACE INTO ads ({fields}) VALUES ({placeholders})"

    conn.execute(sql, values)
    conn.commit()


def insert_photos(conn, ad_id, photo_links):
    sql = "INSERT INTO photos (ad_id, photo_link) VALUES (?, ?)"
    for link in photo_links:
        conn.execute(sql, (ad_id, link))
        conn.commit()


def parse_single_ad(link: str):
    url = urljoin(BASE_URL, link)
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    photo_tag = soup.find("div", class_="carousel-inner").find(
        "script", type="application/ld+json"
    )
    json_images = json.loads(photo_tag.string)

    image_links = [image["contentUrl"] for image in json_images["image"]]
    info_tag = soup.find("script", id="ldJson2", type="application/ld+json")

    json_info = json.loads(info_tag.string)

    id_auto = re.findall(r"\d+", link)[0]
    name = json_info["name"]
    url = json_info["url"]
    price = json_info["offers"]["price"]

    ad_data = {"id_auto": id_auto, "name": name, "url": url, "price": price}

    with create_connection() as conn:
        create_tables(conn)
        insert_ad(conn, ad_data)
        insert_photos(conn, id_auto, image_links)


def parse_ads():
    url = urljoin(BASE_URL, SEARCH_URL)

    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    ticket_items = soup.find_all("section", class_="ticket-item")

    for ticket_item in ticket_items:
        div = ticket_item.find("div", class_="hide")
        link = div.get("data-link-to-view")
        parse_single_ad(link)
        break


if __name__ == "__main__":
    parse_ads()
