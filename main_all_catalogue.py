import time
import os
from os.path import exists
import requests
from pandas import DataFrame
from pandas.io.parsers import TextFileReader
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import holidays
from bdateutil import isbday, relativedelta
import lxml

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


def get_categories(category):
    categories_id = pd.read_csv("milestone_category_subcategory.csv")

    try:
        category_id = categories_id.loc[categories_id["Categories"] == category, "category id"].values[0]
        subcategory_id = categories_id.loc[categories_id["Categories"] == category, "subcategory id"].values[0]
    except IndexError:
        category_id = "2878"
        subcategory_id = "2882"

    return category_id, subcategory_id


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

    raw_df.to_csv("less_raw_df.csv", index=False)
    less_raw_df = pd.read_csv("less_raw_df.csv")
    raw_df_ja = pd.read_csv("test_ja.csv")
    raw_df_ja = raw_df_ja.replace('[()]', '', regex=True)
    raw_df_ja.to_csv("less_raw_df_ja.csv", index=False)
    less_raw_df_ja = pd.read_csv("less_raw_df_ja.csv")
    df = less_raw_df.loc[
        (less_raw_df["Categories"] != "Figure・Doll") & (less_raw_df["Categories"] != "Plastic Model") & (
                less_raw_df["Product status"] != "Tentative Pre-order")]
    df_ja = less_raw_df_ja.loc[(less_raw_df_ja["カテゴリー"] != "フィギュア・ドール") & (less_raw_df_ja["カテゴリー"] != "プラモデル・模型l") & (
            less_raw_df_ja["在庫状況"] != "予約問合せ")]
    return df, df_ja


def create_csv():
    df, df_ja = parse_csv()

    for index, row in df.iterrows():
        # print(row)
        # ami_search = requests.get(f"{AMIAMI_SEARCH}{row['JAN Code']}", headers=headers, cookies=b_cookies)
        product_name = str(row["Product Name"]).replace('"', "").replace("(", "").replace(")", "")
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
        preorder_date = str(row["Pre-order Deadline"]).replace("-", "/")
        print(f'Preorder Date: {preorder_date}')
        ### Checking that the preorder deadline doesn't end on holidays  ###
        while not (isbday(preorder_date, holidays=holidays.Japan())):
            preorder_date = datetime.strptime(preorder_date, "%Y/%m/%d") - timedelta(days=1)
            preorder_date = preorder_date.strftime("%Y/%m/%d")
            print(f"MODIFIED {preorder_date}")

        name_jp_pd = (df_ja.loc[df_ja["JANコード"] == row["JAN Code"]]["商品名"])
        name_jp_str = (str(name_jp_pd))
        name_jp_list = name_jp_str.split()
        name_jp_list.pop(0)
        for x in range(4):
            name_jp_list.pop(-1)
        name_jp = " ".join(name_jp_list)

        maker_list = pd.read_csv("maker_list.csv")
        manufacturer_id = None
        for id_index, id_row in maker_list.iterrows():
            if str(row["Manufacturers"]).lower() == str(id_row["Maker name"]).lower():
                manufacturer_id = id_row["Maker ID"]

        if manufacturer_id is None:
            main_url = "https://anime-export.com/index.php"

            login_data = {
                "command": "login",
                "username": "adminae",
                "password": "cazzinculo6969",
                "x": "57",
                "y": "16",
            }

            new_manufacturers = []
            with requests.Session() as s:
                s.post(main_url, headers=headers, data=login_data)
                manufacturers = s.get("https://anime-export.com/admin/manufacturers.php")
                company = row["Manufacturers"]
                if company not in new_manufacturers:

                    new_data = {"manufacturername": company, "command": "addmanufacturer"}
                    new_manufacturer = s.post("https://anime-export.com/admin/manufacturers.php", data=new_data,
                                              headers=headers)

                    new_manufacturers.append(company)
                    soup = BeautifulSoup(new_manufacturer.content, "lxml")
                    man_ids = soup.find_all("tr", {"style": "background-color: #fff;"})

                    for item in man_ids:
                        if company in str(item):
                            man_id = str(item).split("<td>")[1].split("</td>")[0]
                            manufacturer_id = man_id

                new_csv = s.get("https://anime-export.com/admin/function.php?source=dlmakercsv",
                                allow_redirects=True, headers=headers)
                with open("maker_list.csv", "wb") as file:
                    file.write(new_csv.content)

        category_id, subcategory_id = get_categories(row["Categories"])

        print(category_id)
        print(subcategory_id)
        categories_csv = pd.read_csv("categories_id.csv")
        try:
            category_name = categories_csv.loc[categories_csv["category id"] == category_id, "category"].values[0]
            subcategory_name = \
                categories_csv.loc[categories_csv["subcategory id"] == subcategory_id, "subcategory"].values[0]
        except IndexError:
            category_name = ""
            subcategory_name = ""
        try:
            csv_line_dict = {
                "No": "",
                "Order Type": "Web",
                "product type": "Regular",
                "rank": "NEW",
                "box rank": "NO BOX",
                "jan code": row["JAN Code"],
                "Manufacturer(製品メーカー)": row["Manufacturers"],
                "maker id": manufacturer_id,
                "Name:JP": name_jp,
                "product name": product_name,
                "Name:AE": "",
                "category": category_name,
                "subcategory": subcategory_name,
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
                "1社目:締切日": preorder_date,
            }
        except ValueError:
            csv_line_dict = {
                "No": "",
                "product type": "regular",
                "rank": "new",
                "box rank": "no box",
                "jan code": "",
                "Manufacturer(製品メーカー)": row["Manufacturers"],
                "maker id": manufacturer_id,
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
                "1社目:締切日": preorder_date,

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

        elif str(csv_line_dict["1社目:掛率"]) == "55%" or str(csv_line_dict["1社目:掛率"]) == "56%" or str(
                csv_line_dict["1社目:掛率"]) == "57%":
            csv_line_dict["Paylater discount"] = "25"
            csv_line_dict["Retailer discount"] = "30"
            csv_line_dict["Wholesaler discount"] = "33"
            csv_line_dict["Carton wholesaler discount (%)"] = "33"

        elif str(csv_line_dict["1社目:掛率"]) == "60%" or str(csv_line_dict["1社目:掛率"]) == "61%":
            csv_line_dict["Paylater discount"] = "15"
            csv_line_dict["Retailer discount"] = "25"
            csv_line_dict["Wholesaler discount"] = "30"
            csv_line_dict["Carton wholesaler discount (%)"] = "30"

        elif str(csv_line_dict["1社目:掛率"]) == "62%" or str(csv_line_dict["1社目:掛率"]) == "63%":
            csv_line_dict["Paylater discount"] = "12"
            csv_line_dict["Retailer discount"] = "23"
            csv_line_dict["Wholesaler discount"] = "28"
            csv_line_dict["Carton wholesaler discount (%)"] = "28"

        elif str(csv_line_dict["1社目:掛率"]) == "65%" or str(csv_line_dict["1社目:掛率"]) == "68%":
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

        elif str(csv_line_dict["1社目:掛率"]) == "78%" or str(csv_line_dict["1社目:掛率"]) == "80%":
            csv_line_dict["Paylater discount"] = "0"
            csv_line_dict["Retailer discount"] = "5"
            csv_line_dict["Wholesaler discount"] = "10"
            csv_line_dict["Carton wholesaler discount (%)"] = "10"
        description, material, image_list = amiami_info(csv_line_dict["jan code"])
        print(image_list)
        if description != "":
            description = description.replace(",", ".").replace(";", ".").replace("&amp", "&")
            csv_line_dict["Product description"] = description
        if material != "":
            material = material.replace(",", ".").replace(";", ".").replace("&amp", "&")
            csv_line_dict["Material"] = material

        df2 = pd.DataFrame(csv_line_dict, index=[1])
        desktop = os.path.expanduser("~/Desktop")
        t_file_exists = exists(f"{desktop}\\Milestone preorders-{today}.csv")

        if t_file_exists:

            df2.to_csv(f"{desktop}\\Milestone preorders-{today}.csv", mode="a", header=False,
                       index=False)

        else:

            df2.to_csv(f"{desktop}\\Milestone preorders-{today}.csv", index=False)

        try:
            qty_in_ctn = str(row["Number of Pieces"]).split("=")[1].split(")")[0].replace("pieces", "").replace("packs",
                                                                                                                "").replace(
                "box", "").replace("bags", "").replace("sets", "")
            if "×" in str(qty_in_ctn):
                qty_list = qty_in_ctn.split()
                qty_in_ctn = int(qty_list[0]) * int(qty_list[-1])
                print(qty_in_ctn)
        except IndexError:
            qty_in_ctn = ""
            print(str(row["Number of Pieces"]))
        template_dict = {
            "product name": product_name,
            "jan code": row["JAN Code"],
            "product cost": str(int(row["Wholesale Price"]) * int(row['Order Unit'])),
            "product price": str(int(row["Retail Price"]) * int(row['Order Unit'])),
            "stock qty": "0",
            "max order qty": "6",
            "max global qty": "6",
            "category id": category_id,
            "subcategory id": subcategory_id,
            "weight": "",
            "small packet": "yes",
            "preorder deadline": preorder_date,
            "product release": release_date,
            "Paylater discount": csv_line_dict["Paylater discount"],
            "Retailer discount": csv_line_dict["Retailer discount"],
            "Wholesaler discount": csv_line_dict["Wholesaler discount"],
            "maker id": manufacturer_id,
            "Product scale": "N/A",
            "Material": material.replace(",", "."),
            "Product description": description,
            "image 1": "",
            "image 2": "",
            "image 3": "",
            "image 4": "",
            "image 5": "",
            "image 6": "",
            "image 7": "",
            "image 8": "",
            "image 9": "",
            "image 10": "",
            "product type": "Regular",
            "rank": "NEW",
            "box rank": "NO BOX",
            "wholesaler only": "",
            "creation date": today,
            "size(cm)": "",
            "glue": "",
            "assembly": "",
            "paint": "",
            "qty in carton": qty_in_ctn,
        }
        if len(image_list) != 0:
            counter = 1
            for image in image_list:
                template_dict[f"image {counter}"] = image
                counter += 1

        df = pd.DataFrame(template_dict, index=[1])
        file_exists = exists(f"{desktop}\\Milestone TEMPLATE-{today}.csv")

        if file_exists:

            df.to_csv(f"{desktop}\\Milestone TEMPLATE-{today}.csv", mode="a", header=False,
                      index=False)

        else:

            df.to_csv(f"{desktop}\\Milestone TEMPLATE-{today}.csv", index=False)


def amiami_info(jan):
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    ami_search = driver.get(f"{AMIAMI_SEARCH}{jan}")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "lxml")

    new_items = soup.find("li", {"class": "newly-added-items__item nomore"})
    size = ""
    material = ""
    description = ""
    image_list = []
    if new_items is not None:
        product_link_raw = new_items.find("a")
        product_link = str(product_link_raw).split('href="')[1].split('"')[0]
        print(product_link)
        driver.get(f"https://www.amiami.com{product_link}")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "lxml")
        images = soup.find_all("a", {"class": "nolink"})
        if images is not None:
            ami_tag = product_link.split("gcode=")[1]
            for image in images:
                if ami_tag in str(image):
                    img_link = str(image).split('src="')[1].split('"')[0]
                    image_list.append(img_link)
        if len(image_list) != 0:
            image_list.pop(0)
        while len(image_list) > 10:
            image_list.pop(-1)

        specifications = soup.find_all("dd", {"class": "item-about__data-text"})
        details = soup.find("dd", {"class": "item-about__data-text more"})
        # print(details)
        if details is not None:
            description = str(details).split('"item-about__data-text more">')[1].split("</dd>")[0]
        for specification in specifications:
            if "Size:" in str(specification):
                size = f"Size: {str(specification).split('Size:')[1].split('<')[0]}"
                # print(size)
            if "Material:" in str(specification):
                material = f"{str(specification).split('Material:')[1].split('<')[0]}"
                print(material)
    # print(soup.prettify())
    driver.close()
    description = f"{size} <br/> {description}"
    return description, material, image_list


get_csv()
