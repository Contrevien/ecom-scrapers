from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

ch = os.getcwd() + '/tools/chromedriver'
options = Options()
options.set_headless(headless=True)
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options, executable_path=ch)
keyword = "sport+watch"
sorter = "relevancerank"
driver.get("https://www.google.com")
driver.get_screenshot_as_file('capture.png')
driver.quit()
