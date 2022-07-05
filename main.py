import time
import os
from os.path import exists
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd

import lxml
import re
import csv

service = Service('chromedriver.exe')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

options = Options()
# options.add_argument("--headless")
MAIN_URL = "https://b2b.mile-stone.jp/en/"
USERNAME = "1303700"
PASS = "milestone0730"
LOGIN_PAGE = "https://b2b.mile-stone.jp/en/v1/login/"
b_cookies = {
    "Cookie": "_gid=GA1.2.1654352526.1656855028; language=en; plack_session=f78860c384b7d52e0e706256ddc1345f27ee0bda; "
              "_ga_H9G5GSEWC5=GS1.1.1656855027.1.1.1656855066.0; _ga=GA1.2.204837841.1656855027;"}
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
        # driver.get(f"https://b2b.mile-stone.jp/{csv_language}/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/")
        time.sleep(5)
        cookies = driver.get_cookies()
        for cookie in cookies:
            s.cookies.set(cookie["name"], cookie["value"])

        soup = BeautifulSoup(driver.page_source, "lxml")
        # print(soup.prettify())

        # new_items = soup.find("div", {"class": "api-new-products"})
        # print(new_items)
        # print(len(new_items))
        # milestone_code = new_items.find_all("data-mscode")
        # print(milestone_code)
        driver.close()
        return s


def get_csv():
    print(today)
    print(yesterday)
    s = login()

    search_url = s.get(
        f"https://b2b.mile-stone.jp/{csv_language}/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/?format=csv",
        allow_redirects=True, headers=headers)
    search_url_ja = s.get(
        f"https://b2b.mile-stone.jp/ja/search/0/date_type=guiduncedOn/date_span={yesterday}-{today}/status=preOrder/?format=csv",
        allow_redirects=True, headers=headers)

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
    # print(raw_df)
    df = less_raw_df.loc[(less_raw_df["Categories"] != "Figure・Doll") & (less_raw_df["Categories"] != "Plastic Model")]
    df_ja = less_raw_df_ja.loc[(less_raw_df_ja["カテゴリー"] != "フィギュア・ドール") & (less_raw_df_ja["カテゴリー"] != "プラモデル・模型l")]
    return df, df_ja
    # print(df.to_string())


def create_csv():
    df, df_ja = parse_csv()

    for index, row in df.iterrows():
        # print(row)
        ami_search = requests.get(f"{AMIAMI_SEARCH}{row['JAN Code']}", headers=headers, cookies=b_cookies)
        product_name = str(row["Product Name"]).replace('"', "")
        if row["Order Unit"] != 1:
            product_name = f"{product_name} ({row['Order Unit']} pieces)"

        month = int(row["Release Date"].split("/")[1])
        short_months = [9, 4, 6, 11]
        if month == 2:
            day = "28"
        elif month in short_months:
            day = "30"
        else:
            day = "31"

        if "Within " in str(row["Release Date"]):
            release_date = f'{str(row["Release Date"]).replace("Within ", "")}/{day}'
        else:
            release_date = str(row["Release Date"])

        try:
            csv_line_dict = {
                "No": "",
                "Order Type": "Web",
                "product type": "Regular",
                "rank": "NEW",
                "box rank": "NO BOX",
                "jan code": row["JAN Code"],
                "Manufacturer(製品メーカー)": row["Manufacturers"],
                "maker id": "",
                "Name:JP": str(df_ja.loc[df_ja["JANコード"] == row["JAN Code"]]["商品名"]).split("\n")[0][6:],
                "product name": product_name,
                "Name:AE": "",
                "category": "",
                "subcategory": "",
                "preorder deadline": "",
                "product release": release_date,
                "Discount(%)": "",
                "product price": str(int(row["Retail Price"]) * int(row['Order Unit'])),
                "product cost": str(int(row["Wholesale Price"]) * int(row['Order Unit'])),
                "Order Date": "",
                "合計発注数": "",
                "stock qty": "0",
                "max order qty": "3",
                "max global qty": "180",
                "Product scale": "N/A",
                "Product Weight (g)": "",
                "Product Single Packed Weight (g)": "",
                "small packet": "yes",
                "DHL box": "",
                "size(cm)": "",
                "Paylater discount": "",
                "Retailer discount": "",
                "Wholesaler discount": "",
                "Carton wholesaler discount (%)": "",
                "qty in carton": "",
                "": "",
                "Material": "ABS, PVC",
                "wholesaler only": "",
                "Product description": "",
                "assembly": "",
                "glue": "",
                "paint": "",
                "再販": "",
                "Reissue": "",
                "再販(Re)": "",
                "category id": "",
                "subcategory id": "",
                "creation date": "",
                "Note": "",
                "1社目:数量": "",
                "1社目:発注先": "Milestone",
                "1社目:掛率": f'{round(((int(row["Wholesale Price"]) * int(row["Order Unit"])) / int((row["Retail Price"]) * int(row["Order Unit"])) * 100))}%',
                "1社目:締切日": str(row["Pre-order Deadline"]).replace("-", "/"),
            }
        except ValueError:
            csv_line_dict = {
                "No": "",
                "product type": "regular",
                "rank": "new",
                "box rank": "no box",
                "jan code": "",
                "Manufacturer(製品メーカー)": row["Manufacturers"],
                "maker id": "",
                "Name:JP": str(df_ja.loc[df_ja["JANコード"] == row["JAN Code"]]["商品名"]).split("\n")[0][6:],
                "product name": product_name,
                "Name:AE": "",
                "category": "",
                "subcategory": "",
                "preorder deadline": "",
                "product release": release_date,
                "Discount(%)": "",
                "product price": str(int(row["Retail Price"]) * int(row['Order Unit'])),
                "product cost": str(int(row["Wholesale Price"]) * int(row['Order Unit'])),
                "Order Date": "",
                "合計発注数": "",
                "stock qty": "0",
                "max order qty": "3",
                "max global qty": "180",
                "Product scale": "N/A",
                "Product Weight (g)": "",
                "Product Single Packed Weight (g)": "",
                "small packet": "yes",
                "DHL box": "",
                "size(cm)": "",
                "Paylater discount": "",
                "Retailer discount": "",
                "Wholesaler discount": "",
                "Carton wholesaler discount (%)": "",
                "qty in carton": "",
                "": "",
                "Material": "ABS, PVC",
                "wholesaler only": "",
                "Product description": "",
                "assembly": "",
                "glue": "",
                "paint": "",
                "再販": "",
                "Reissue": "",
                "再販(Re)": "",
                "category id": "",
                "subcategory id": "",
                "creation date": "",
                "Note": "",
                "1社目:数量": "",
                "1社目:発注先": "Milestone",
                "1社目:掛率": f'{round(((int(row["Wholesale Price"]) * int(row["Order Unit"])) / int((row["Retail Price"]) * int(row["Order Unit"])) * 100))}%',
                "1社目:締切日": str(row["Pre-order Deadline"]).replace("-", "/"),

            }

        if str(csv_line_dict["1社目:掛率"]) == "28%":
            csv_line_dict["Paylater discount"] = "20"
            csv_line_dict["Retailer discount"] = "25"
            csv_line_dict["Wholesaler discount"] = "30"
            csv_line_dict["Carton wholesaler discount (%)"] = "30"

        elif str(csv_line_dict["1社目:掛率"]) == "50%":
            csv_line_dict["Paylater discount"] = "30"
            csv_line_dict["Retailer discount"] = "35"
            csv_line_dict["Wholesaler discount"] = "40"
            csv_line_dict["Carton wholesaler discount (%)"] = "40"

        elif str(csv_line_dict["1社目:掛率"]) == "57%":
            csv_line_dict["Paylater discount"] = "25"
            csv_line_dict["Retailer discount"] = "30"
            csv_line_dict["Wholesaler discount"] = "33"
            csv_line_dict["Carton wholesaler discount (%)"] = "33"

        elif str(csv_line_dict["1社目:掛率"]) == "60%":
            csv_line_dict["Paylater discount"] = "15"
            csv_line_dict["Retailer discount"] = "25"
            csv_line_dict["Wholesaler discount"] = "30"
            csv_line_dict["Carton wholesaler discount (%)"] = "30"

        elif str(csv_line_dict["1社目:掛率"]) == "62%":
            csv_line_dict["Paylater discount"] = "12"
            csv_line_dict["Retailer discount"] = "23"
            csv_line_dict["Wholesaler discount"] = "28"
            csv_line_dict["Carton wholesaler discount (%)"] = "28"

        elif str(csv_line_dict["1社目:掛率"]) == "65%":
            csv_line_dict["Paylater discount"] = "15"
            csv_line_dict["Retailer discount"] = "20"
            csv_line_dict["Wholesaler discount"] = "25"
            csv_line_dict["Carton wholesaler discount (%)"] = "25"

        elif str(csv_line_dict["1社目:掛率"]) == "70%":
            csv_line_dict["Paylater discount"] = "5"
            csv_line_dict["Retailer discount"] = "10"
            csv_line_dict["Wholesaler discount"] = "20"
            csv_line_dict["Carton wholesaler discount (%)"] = "20"

        elif str(csv_line_dict["1社目:掛率"]) == "72%":
            csv_line_dict["Paylater discount"] = "7"
            csv_line_dict["Retailer discount"] = "12"
            csv_line_dict["Wholesaler discount"] = "18"
            csv_line_dict["Carton wholesaler discount (%)"] = "18"

        elif str(csv_line_dict["1社目:掛率"]) == "75%":
            csv_line_dict["Paylater discount"] = "5"
            csv_line_dict["Retailer discount"] = "10"
            csv_line_dict["Wholesaler discount"] = "15"
            csv_line_dict["Carton wholesaler discount (%)"] = "15"

        elif str(csv_line_dict["1社目:掛率"]) == "80%":
            csv_line_dict["Paylater discount"] = "0"
            csv_line_dict["Retailer discount"] = "5"
            csv_line_dict["Wholesaler discount"] = "10"
            csv_line_dict["Carton wholesaler discount (%)"] = "10"

        df = pd.DataFrame(csv_line_dict, index=[1])
        desktop = os.path.expanduser("~/Desktop")
        file_exists = exists(f"{desktop}\\Milestone preorders-{today}.csv")

        if file_exists:

            df.to_csv(f"{desktop}\\Milestone preorders-{today}.csv", mode="a", header=False,
                      index=False)

        else:

            df.to_csv(f"{desktop}\\Milestone preorders-{today}.csv", index=False)
        soup = BeautifulSoup(ami_search.content, "lxml")
        # print(soup.prettify())
        print(csv_line_dict)


def percentage(discount):
    wholesaler_disc = ((discount / 100) * 100) - 10


get_csv()
