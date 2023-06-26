import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests as requests


BASE_URL = "https://auto.ria.com"
SEARCH_URL = "search/?indexName=auto&categories.main.id=1&brand.id[0]=79&model.id[0]=2104&country.import.usa.not=0&price.currency=1&abroad.not=0&custom.not=1&damage.not=0&page=0&size=1000"


def parse_single_ad(link: str):
    url = urljoin(BASE_URL, link)
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    photo_tag = soup.find("div", class_="carousel-inner").find(
        "script", type="application/ld+json"
    )
    json_images = json.loads(photo_tag.string)

    image_links = [image["contentUrl"] for image in json_images["image"]]

    for link in image_links:
        print(link)

    info_tag = soup.find("script", id="ldJson2", type="application/ld+json")

    json_info = json.loads(info_tag.string)

    name = json_info["name"]
    url = json_info["url"]
    price = json_info["offers"]["price"]

    print("Name:", name)
    print("URL:", url)
    print("Price:", price)


def parse_ads():
    url = urljoin(BASE_URL, SEARCH_URL)

    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    ticket_items = soup.find_all("section", class_="ticket-item")

    for ticket_item in ticket_items:
        div = ticket_item.find("div", class_="hide")
        link = div.get("data-link-to-view")
        parse_single_ad(link)


if __name__ == "__main__":
    parse_ads()
