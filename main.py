import time

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from requests_html import HTMLSession
import lxml
import re
import csv
service = Service('chromedriver.exe')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

options = Options()
# options.add_argument("--headless")
MAIN_URL = "https://b2b.mile-stone.jp/en/"
USERNAME = "1303700"
PASS = "milestone0730"
LOGIN_PAGE = "https://b2b.mile-stone.jp/en/v1/login/"
cookies = {
    "Cookie": "_gid=GA1.2.1271725439.1655944541; language=en; plack_session=37d07e856458ae2f3b71c2dbc9aeba7b131ae63d; "
              "_ga_H9G5GSEWC5=GS1.1.1655991150.2.1.1655991957.0; _ga=GA1.2.1103772324.1655944541; GDPR=accept",
    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"}
csv_language = "en"
today = datetime.now()
yesterday = today - timedelta(days=1)
today = datetime.strftime(today, "%Y-%m-%d")
yesterday = datetime.strftime(yesterday, "%Y-%m-%d")
AMIAMI_SEARCH = "https://www.amiami.com/eng/search/list/?s_keywords="
def login():
    with requests.Session() as s:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(LOGIN_PAGE)
        username = driver.find_element(By.NAME, "account")
        username.click()
        username.send_keys(USERNAME)
        password = driver.find_element(By.NAME, "passphrase")
        password.click()
        password.send_keys(PASS)
        enter_btn = driver.find_element(By.NAME, "login")
        enter_btn.click()
        #driver.get(f"https://b2b.mile-stone.jp/{csv_language}/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/")
        time.sleep(5)
        cookies = driver.get_cookies()
        for cookie in cookies:
            s.cookies.set(cookie["name"], cookie["value"])

        soup = BeautifulSoup(driver.page_source, "lxml")
        #print(soup.prettify())

        new_items = soup.find("div", {"class": "api-new-products"})
        print(new_items)
        #print(len(new_items))
        milestone_code = new_items.find_all("data-mscode")
        print(milestone_code)
        driver.close()
        return s


def get_csv():
    print(today)
    print(yesterday)
    s = login()

    search_url = s.get(
        f"https://b2b.mile-stone.jp/{csv_language}/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/?format=csv", allow_redirects=True, headers=headers)
    search_url_ja = s.get(
        f"https://b2b.mile-stone.jp/ja/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/?format=csv", allow_redirects=True, headers=headers)

    with open("test.csv", "wb") as file:
        file.write(search_url.content)
    with open("test_ja.csv", "wb") as file:
        file.write(search_url_ja.content)

    create_csv()

def parse_csv():
    raw_df = pd.read_csv("test.csv")
    raw_df = raw_df.replace('[()]', '', regex=True)
    raw_df.to_csv("less_raw_df.csv", index=False)
    less_raw_df = pd.read_csv("less_raw_df.csv")
    raw_df_ja = pd.read_csv("test_ja.csv")
    raw_df_ja = raw_df_ja.replace('[()]', '', regex=True)
    raw_df_ja.to_csv("less_raw_df_ja.csv", index=False)
    less_raw_df_ja = pd.read_csv("less_raw_df_ja.csv")
    #print(raw_df)
    df = less_raw_df.loc[(less_raw_df["Categories"] != "Figure・Doll") & (less_raw_df["Categories"] != "Plastic Model")]
    df_ja = less_raw_df_ja.loc[(less_raw_df_ja["カテゴリー"] != "フィギュア・ドール") & (less_raw_df_ja["カテゴリー"] != "プラモデル・模型l")]
    return df, df_ja
    #print(df.to_string())


def create_csv():

    df, df_ja = parse_csv()

    for index, row in df.iterrows():
        #print(row)
        ami_search = requests.get(f"{AMIAMI_SEARCH}{row['JAN Code']}", headers=headers, cookies=cookies)
        product_name = str(row["Product Name"]).replace('"', "")
        if row["Order Unit"] != "1":
            product_name = f"{product_name} ({row['Order Unit']} pieces Set)"
        csv_line_dict = {
            "No": "",
            "product type": "regular",
            "rank": "new",
            "box rank": "no box",
            "jan code": row["JAN Code"],
            "Manufacturer(製品メーカー)": row["Manufacturers"],
            "maker id": "",
            "Name:JP": str(df_ja.loc[df_ja["JANコード"] == row["JAN Code"]]["商品名"]).split("\n")[0][7:],
            "product name": product_name,
            "Name:AE": "",
            "category": "",
            "subcategory": "",
            "preorder deadline": row["Pre-order Deadline"],
            "product release": row["Release Date"],
            "Discount(%)": "",
            "product price": str(int(row["Retail Price"]) * int(row['Order Unit'])),
            "product cost": str(int(row["Wholesale Price"]) * int(row['Order Unit'])),
            "Order Date": "",
            "合計発注数": "",
            "stock qty": "0",
            "max order qty": "3",
            "max global qty": "180",
            "Product scale": "",
            "Product Weight (g)": "",
            "Product Single Packed Weight (g)": "",
            "small packet": "yes",
            "DHL box": "",
            "size(cm)": "",
            "Paylater discount": "",
            "Retailer discount": "",
            "Wholesaler discount": "",
            "Material": "",
            "Product description": "",
            "Image 1": "",
            "Image 2": "",
            "Image 3": "",
            "Image 4": "",
            "Image 5": "",
            "Image 6": "",
            "Image 7": "",
            "Image 8": "",
            "Image 9": "",
            "Image 10": "",
            "wholesaler only": "",
            "creation date": "",
            "glue": "",
            "assembly": "",
            "paint": "",
            "qty in carton": "",
        }
        soup = BeautifulSoup(ami_search.content, "lxml")
        print(soup.prettify())
get_csv()
