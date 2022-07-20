from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.service import Service
from selenium import webdriver

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/39.0.2171.95 Safari/537.36'}
main_url = "https://anime-export.com/index.php"

login_data = {
    "command": "login",
    "username": "adminae",
    "password": "cazzinculo6969",
    "x": "57",
    "y": "16",
}
url = "https://anime-export.com/admin/csvupload.php"
files = {"upload_file": open("anvil.png", "rb")}
values = {"DB": "photcat", "OUT": "csv", "SHORT": "short"}

with requests.Session() as s:
    s.post(main_url, headers=headers, data=login_data)
    manufacturers = s.get("https://anime-export.com/admin/manufacturers.php")
    company = "test"
    new_data = {"manufacturername": company, "command": "addmanufacturer"}
    new_manufacturer = s.post("https://anime-export.com/admin/manufacturers.php", data=new_data, headers=headers)
    soup = BeautifulSoup(new_manufacturer.content, "lxml")
    man_ids = soup.find_all("tr", {"style": "background-color: #fff;"})
    for item in man_ids:
        if company in str(item):
            man_id = str(item).split("<td>")[1].split("</td>")[0]
