import os
from os.path import exists

import holidays
from bdateutil import isbday
from flask import Flask, request, redirect, url_for, render_template
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import pandas as pd

service = Service('chromedriver.exe')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
main_url = "https://anime-export.com/index.php"
desktop = os.path.expanduser("~/Desktop")
login_data = {
    "command": "login",
    "username": os.environ['AEX_USERNAME'],
    "password": os.environ['AEX_PASS'],
    "x": "57",
    "y": "16",
}
options = Options()
# options.add_argument("--headless")
MAIN_URL = "https://b2b.mile-stone.jp/en/"
USERNAME = os.environ['MILESTONE_USERNAME']
PASS = os.environ['MILESTONE_PASS']
LOGIN_PAGE = "https://b2b.mile-stone.jp/en/v1/login/"
AMIAMI_SEARCH = "https://www.amiami.com/eng/search/list/?s_keywords="
csv_language = "en"
today = datetime.now()
yesterday = today - timedelta(days=3)
today = datetime.strftime(today, "%Y-%m-%d")
yesterday = datetime.strftime(yesterday, "%Y-%m-%d")

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
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
        time.sleep(6)
        cookies = driver.get_cookies()
        for cookie in cookies:
            s.cookies.set(cookie["name"], cookie["value"])

        soup = BeautifulSoup(driver.page_source, "lxml")

        new_items = soup.find("div", {"class": "api-new-products"})

        for a_tag in new_items.find_all("a", href=True):
            a_tag["href"] = a_tag["href"].replace("/en/", "https://b2b.mile-stone.jp/en/")
        for img in new_items.find_all("img"):
            try:
                img_link = (str(img).split('data-original="')[1].split('"')[0])
            except IndexError:
                img_link = ""
            img["src"] = img_link
        driver.close()
        new_items_list_raw = str(new_items).split('<div class="col-xs-2">')
        new_items_list = []
        new_items_list_raw.pop(0)

        counter = 1
        for row in new_items_list_raw:
            row_soup = BeautifulSoup(row, "lxml")
            try:
                ms_code = str(row_soup.find("a", href=True)).split('<a href="')[1].split('"')[0]
            except IndexError:
                ms_code = "dud"
            # print(ms_code)

            row = row.replace('<div class="thumbnail"', '<div class="col-sm-4" style="background-color:lavender;"> '
                                                        '<div class="thumbnail"').replace(
                '<li>??</li></ul></div></div></div>', '<li><br>Add to csv <input type="checkbox" name="mycheckbox" '
                                                     f'value="{ms_code}"></li'
                                                     '></ul></div></div></div>').replace('<div class="row"></div>', '')

            if '/groups/' in ms_code:
                row = row.replace('</ul></div></div></div>', '<li><br>Add to csv <input type="checkbox" '
                                                             'name="mycheckbox" '
                                                             f'value="{ms_code}"></li></ul></div></div></div>')
            if counter % 3 == 0:
                row = f'</div> <div class="row">  {row}'

            new_items_list.append(row)
            counter += 1

        new_items = " ".join(new_items_list)

        get_csv(s)

        return render_template("test.html", new_items=new_items)


@app.route("/get_results", methods=["GET", "POST"])
def get_results():
    if request.method == "POST":
        flask_list = request.form.getlist('mycheckbox')

        for link in flask_list:
            if '/groups/' in link:

                s = requests.get(link)
                soup = BeautifulSoup(s.content, "lxml")
                bundle_links = []
                links = (soup.find_all("a"))
                print(flask_list)
                for item in links:
                    if "/en/products/" in str(item) and "/groups/" not in str(item):
                        product_link = f'https://b2b.mile-stone.jp{item["href"]}'
                        bundle_links.append(product_link)
                flask_list.remove(link)
                for group_link in bundle_links:
                    flask_list.append(group_link)
                print(flask_list)
    create_csv(flask_list)
    return "Done"


def get_csv(s):
    print(today)
    print(yesterday)

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


def parse_csv():
    raw_df = pd.read_csv("test.csv")

    raw_df.to_csv("less_raw_df.csv", index=False)
    less_raw_df = pd.read_csv("less_raw_df.csv")
    raw_df_ja = pd.read_csv("test_ja.csv")
    raw_df_ja = raw_df_ja.replace('[()]', '', regex=True)
    raw_df_ja.to_csv("less_raw_df_ja.csv", index=False)
    less_raw_df_ja = pd.read_csv("less_raw_df_ja.csv")

    return less_raw_df, less_raw_df_ja


def create_csv(flask_list):
    df, df_ja = parse_csv()
    df = df.loc[df["URL"].isin(flask_list)]
    print(df)
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

        if isbday(preorder_date, holidays=holidays.Japan()):
            preorder_date = datetime.strptime(preorder_date, "%Y/%m/%d") + timedelta(days=1)
            preorder_date = preorder_date.strftime("%Y/%m/%d")
            print(f"MODIFIED {preorder_date}")

        while not (isbday(preorder_date, holidays=holidays.Japan())):
            preorder_date = datetime.strptime(preorder_date, "%Y/%m/%d") - timedelta(days=1)
            preorder_date = preorder_date.strftime("%Y/%m/%d")
            print(f"MODIFIED {preorder_date}")

        name_jp_pd = (df_ja.loc[df_ja["JAN?????????"] == row["JAN Code"]]["?????????"])
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
                "Manufacturer(??????????????????)": row["Manufacturers"],
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
                "???????????????": "",
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
                "??????": "",
                "Reissue": "",
                "??????(Re)": "",
                "category id": "",
                "subcategory id": "",
                "creation date": "",
                "Note": "",
                "1??????:??????": "",
                "1??????:?????????": "Milestone",
                "1??????:??????": f'{round(((int(row["Wholesale Price"]) * int(row["Order Unit"])) / int((row["Retail Price"]) * int(row["Order Unit"])) * 100))}%',
                "1??????:?????????": preorder_date,
            }
        except ValueError:
            csv_line_dict = {
                "No": "",
                "product type": "regular",
                "rank": "new",
                "box rank": "no box",
                "jan code": "",
                "Manufacturer(??????????????????)": row["Manufacturers"],
                "maker id": manufacturer_id,
                "Name:JP": str(df_ja.loc[df_ja["JAN?????????"] == row["JAN Code"]]["?????????"]).split("\n")[0][6:],
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
                "???????????????": "",
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
                "??????": "",
                "Reissue": "",
                "??????(Re)": "",
                "category id": "",
                "subcategory id": "",
                "creation date": "",
                "Note": "",
                "1??????:??????": "",
                "1??????:?????????": "Milestone",
                "1??????:??????": f'{round(((int(row["Wholesale Price"]) * int(row["Order Unit"])) / int((row["Retail Price"]) * int(row["Order Unit"])) * 100))}%',
                "1??????:?????????": preorder_date,

            }

        if str(csv_line_dict["1??????:??????"]) == "28%":
            csv_line_dict["Paylater discount"] = "20"
            csv_line_dict["Retailer discount"] = "25"
            csv_line_dict["Wholesaler discount"] = "30"
            csv_line_dict["Carton wholesaler discount (%)"] = "30"

        elif str(csv_line_dict["1??????:??????"]) == "50%":
            csv_line_dict["Paylater discount"] = "30"
            csv_line_dict["Retailer discount"] = "35"
            csv_line_dict["Wholesaler discount"] = "40"
            csv_line_dict["Carton wholesaler discount (%)"] = "40"

        elif str(csv_line_dict["1??????:??????"]) == "55%" or str(csv_line_dict["1??????:??????"]) == "56%" or str(
                csv_line_dict["1??????:??????"]) == "57%":
            csv_line_dict["Paylater discount"] = "25"
            csv_line_dict["Retailer discount"] = "30"
            csv_line_dict["Wholesaler discount"] = "33"
            csv_line_dict["Carton wholesaler discount (%)"] = "33"

        elif str(csv_line_dict["1??????:??????"]) == "60%" or str(csv_line_dict["1??????:??????"]) == "61%":
            csv_line_dict["Paylater discount"] = "15"
            csv_line_dict["Retailer discount"] = "25"
            csv_line_dict["Wholesaler discount"] = "30"
            csv_line_dict["Carton wholesaler discount (%)"] = "30"

        elif str(csv_line_dict["1??????:??????"]) == "62%" or str(csv_line_dict["1??????:??????"]) == "63%":
            csv_line_dict["Paylater discount"] = "12"
            csv_line_dict["Retailer discount"] = "23"
            csv_line_dict["Wholesaler discount"] = "28"
            csv_line_dict["Carton wholesaler discount (%)"] = "28"

        elif str(csv_line_dict["1??????:??????"]) == "65%" or str(csv_line_dict["1??????:??????"]) == "68%":
            csv_line_dict["Paylater discount"] = "15"
            csv_line_dict["Retailer discount"] = "20"
            csv_line_dict["Wholesaler discount"] = "25"
            csv_line_dict["Carton wholesaler discount (%)"] = "25"

        elif str(csv_line_dict["1??????:??????"]) == "70%":
            csv_line_dict["Paylater discount"] = "5"
            csv_line_dict["Retailer discount"] = "10"
            csv_line_dict["Wholesaler discount"] = "20"
            csv_line_dict["Carton wholesaler discount (%)"] = "20"

        elif str(csv_line_dict["1??????:??????"]) == "72%":
            csv_line_dict["Paylater discount"] = "7"
            csv_line_dict["Retailer discount"] = "12"
            csv_line_dict["Wholesaler discount"] = "18"
            csv_line_dict["Carton wholesaler discount (%)"] = "18"

        elif str(csv_line_dict["1??????:??????"]) == "75%":
            csv_line_dict["Paylater discount"] = "5"
            csv_line_dict["Retailer discount"] = "10"
            csv_line_dict["Wholesaler discount"] = "15"
            csv_line_dict["Carton wholesaler discount (%)"] = "15"

        elif str(csv_line_dict["1??????:??????"]) == "78%" or str(csv_line_dict["1??????:??????"]) == "80%":
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
            if "??" in str(qty_in_ctn):
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

    aex_upload()


def aex_upload():
    with requests.Session() as s:
        s.post(main_url, headers=headers, data=login_data)

        files = {"upload_file": open("1659082051_59503_25_anvil.png", "rb")}
        values = {'dir': '/product_images/', 'submit': 'Submit'}
        mierda = s.post("https://anime-export.com/admin/addpicpanel.php?product_id=59503", files=files, data=values)
        csv_upload_page = s.get("https://anime-export.com/admin/addpicpanel.php?product_id=59503")
        soup = BeautifulSoup(csv_upload_page.content, "lxml")
        print(soup.prettify)
        print(mierda)


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


def get_categories(category):
    categories_id = pd.read_csv("milestone_category_subcategory.csv")

    try:
        category_id = categories_id.loc[categories_id["Categories"] == category, "category id"].values[0]
        subcategory_id = categories_id.loc[categories_id["Categories"] == category, "subcategory id"].values[0]
    except IndexError:
        category_id = "2878"
        subcategory_id = "2882"

    return category_id, subcategory_id


if __name__ == "__main__":
    app.run(debug=True)
