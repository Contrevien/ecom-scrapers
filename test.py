import os
import json
import requests
from time import sleep
from bs4 import BeautifulSoup as bs

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

sorters = ["popularity-rank", "price-asc-rank",
           "price-desc-rank", "review-rank", "date-desc-rank"]

keyword = "sport+watch"
sorter = sorters[3]

url = "https://www.amazon.in/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=" + \
    keyword + "&&sort=" + sorter
page = requests.get(url, headers={"User-Agent": "Defined"})
soup = bs(page.content, "html.parser")
print(soup.find(id="result_0").text())
