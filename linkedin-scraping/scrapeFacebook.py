from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import urllib.request
import time
import json
from pymongo import MongoClient


userid = "akkimysite@gmail.com"
password = "anzcallahan\n"

timestamp = int(time.time())
ch = os.getcwd() + '/tools/chromedriver'
options = Options()
options.add_argument("log-level=3")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options, executable_path=ch)
wait = WebDriverWait(driver, 10)
driver.implicitly_wait(0.5)
driver.get("https://www.facebook.com/")
errors = {}
client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

def login():
    wait.until(EC.presence_of_element_located((By.ID, "pass")))
    driver.find_element_by_id("email").send_keys(userid)
    driver.find_element_by_id("pass").send_keys(password)

login()
driver.find_element_by_tag_name("body").send_keys(Keys.ESCAPE)
for x in scraperDb.persons.find({}):
    keyword = "+".join(x["keyword"].split())
    driver.get("https://www.facebook.com/search/str/" + keyword + "/keywords_users")
    try:
        total = driver.find_element_by_id("BrowseResultsContainer")
        
        print(total.find_elements_by_tag_name("a").get_attribute("href"))
    except:
        pass