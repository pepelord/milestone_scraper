from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.service import Service
from selenium import webdriver

options = Options()
# options.add_argument("--headless")

service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

b_cookies = {
    "Cookie": "_gid=GA1.2.1654352526.1656855028; language=en; plack_session=f78860c384b7d52e0e706256ddc1345f27ee0bda; "
              "_ga_H9G5GSEWC5=GS1.1.1656855027.1.1.1656855066.0; _ga=GA1.2.204837841.1656855027;"}
csv_language = "en"
today = datetime.now()
yesterday = today - timedelta(days=1)
today = datetime.strftime(today, "%Y-%m-%d")
yesterday = datetime.strftime(yesterday, "%Y-%m-%d")
AMIAMI_SEARCH = "https://www.amiami.com/eng/search/list/?s_keywords="

ami_search = driver.get("https://www.amiami.com/eng/search/list/?s_keywords=4582615812668")
# ami_search = requests.get(f"{AMIAMI_SEARCH}4582615812668", headers=headers)
print(ami_search)
# soup = BeautifulSoup(ami_search.page_source, "html.parser")
driver.quit()
# print(soup.prettify())
