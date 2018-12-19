from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
import json
from pymongo import MongoClient
import platform
from psutil import virtual_memory
from subprocess import check_output
import sys

currencyMap = {
    "US": "USD",
    "IN": "INR",
    "FR": "EUR",
    "IT": "EUR"
}

ch = os.getcwd() + '/tools/chromedriver'
options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
# options.add_extension('test.crx')
options.set_headless(headless=True)
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("log-level=3")
# driver = webdriver.Chrome(options=options, executable_path=ch)
# wait = WebDriverWait(driver, 10)

timestamp = int(time.time())
errors = {}

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

def getRankAndSeller():
    done = False
    i = 0
    while not done:
        obj = scraperDb.bestSellers.find({"obj_id": i})
        if obj.count() == 0:
            done = True
        else:
            for o in obj:
                if "Amazon" in o["levels"][0]:
                    o["seller"] = "Amazon"
                    o["bestSellersRank"] = "NA"
                print(o)
        break

getRankAndSeller()