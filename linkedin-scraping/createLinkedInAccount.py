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
driver.get("https://www.linkedin.com/")
errors = {}
client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

driver.find_element_by_id("reg-firstname").send_keys("Nulabs")
driver.find_element_by_id("reg-lastname").send_keys("Official")
driver.find_element_by_id("reg-email").send_keys("sanzerinf@gmail.com")
driver.find_element_by_id("reg-password").send_keys("dontplease")
driver.find_element_by_id("registration-submit").click()
