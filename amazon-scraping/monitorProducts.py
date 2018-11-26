from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import urllib.request
import time
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from psutil import virtual_memory
import platform
from subprocess import check_output
# from scrapeAmazon import get_detailed_ratings


ch = os.getcwd() + '/tools/chromedriver'
options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
# options.set_headless(headless=True)
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("log-level=3")
driver = webdriver.Chrome(options=options, executable_path=ch)
wait = WebDriverWait(driver, 10)

timestamp = int(time.time())
errors = {}

client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def get_price(marketPlace):
    try:
        price = driver.find_element_by_id("priceblock_ourprice").text
        if marketPlace == "US":
            return float("".join(price[1:].split(",")))
        if marketPlace == "IN":
            price = "".join(price.strip().split(","))
            return float(price)
        if marketPlace == "FR":
            price = price.split()[1:]
            final = ".".join(price[-1].split(","))
            final = "".join(price[:-1]) + final
            return float(final)
        if marketPlace == "IT":
            price = price[4:]
            price = "".join(price.split("."))
            price = ".".join(price.split(","))
            return float(price)
    except:
        return "NA"


def get_ratings(marketPlace):
    try:
        revs = driver.find_element_by_id("reviewsMedley")
        yo = revs.text
        if not yo[0].isdigit():
            return "NA"
        if marketPlace == "US" or marketPlace == "IN":
            return float(yo.split("\n")[1].split()[0])
        if marketPlace == "FR" or marketPlace == "IT":
            return float(".".join(yo.split("\n")[1].split()[0].split(",")))
        return "NA"
    except:
        return "NA"


def get_detailed_ratings():
    try:
        review = wait.until(
            EC.presence_of_element_located((By.ID, "reviewsMedley")))
        table = review.find_element_by_id("histogramTable")
        percents = table.find_elements_by_class_name("a-text-right")
        review_arr = []
        for i in percents:
            review_arr.append(int(i.text[:-1]))
        ratings = dict()
        for i in range(5):
            ratings[str(5-i)+"stars"] = review_arr[i]
        return ratings
    except:
        return "NA"


def get_reviews(marketPlace):
    try:
        revs = driver.find_element_by_id("reviewsMedley")
        yo = revs.text
        if not yo[0].isdigit():
            return "NA"
        reviews = yo.split("\n")[0].split()[0]
        if marketPlace == "IN" or marketPlace == "US":
            return int("".join(reviews.split(",")))
        if marketPlace == "IT":
            return int("".join(reviews.split(".")))
        if marketPlace == "FR":
            reviews = ""
            i = 0
            while yo[i].isdigit() or yo[i] == " ":
                reviews += yo[i]
                i += 1
            return int("".join(reviews.split()))
        return "NA"
    except:
        return "NA"

def get_avg_ratings(el):
    try:
        text = el.find_element_by_tag_name("i").get_attribute("class").split()[-1]
        if "a-star" not in text:
            text = el.find_elements_by_tag_name("i")[1].get_attribute("class").split()[-1]
        text = text.split("-")
        rating = ""
        for x in text:
            if x.isdigit():
                rating += x + " "
        if "avg-rating" in errors.keys():
            errors["avg-rating"] = 0
        return float(".".join(rating.split()))
    except:
        if "avg-rating" in errors.keys():
            errors["avg-rating"] += 1
        else:
            errors["avg-rating"] = 1
        return "NA"

def separate_price_and_currency(value, marketPlace):
    if "-" in value:
        value = value.split("-")
        value = value[0].strip()
    if marketPlace == "US":
        if "," in value:
            value = "".join(value.split(","))
        return ["USD", float(value[1:])]
    if marketPlace == "IN":
        if "," in value:
            value = "".join(value.split(","))
        return ["INR", float(value)]
    if marketPlace == "FR":
        value = value.split()[1:]
        value = "".join(value)
        value = ".".join(value.split(","))
        return ["EUR", float(value)]
    if marketPlace == "IT":
        value = value.split()[1:]
        value = value[0]
        value = "".join(value.split("."))
        value = ".".join(value.split(","))
        return ["EUR", float(value)]

    return ["NA", "NA"]


def scrape_also_bought_element(el, marketPlace):
    details = dict()
    dets = el.text.split("\n")
    details["title"] = dets[0]
    a = el.find_elements_by_tag_name("a")
    try:
        for span in el.find_elements_by_tag_name("span"):
            if "a-color-price" in span.get_attribute("class"):
                details["currency"], details["price"] = separate_price_and_currency(span.text, marketPlace)
    except:
        details["currency"], details["price"] = ["NA", "NA"]

    details["htmlLinkPage"] = a[0].get_attribute("href")
    details["ratingOf5stars"] = get_avg_ratings(el)
    try:
        details["customersReviewsCount"] = int("".join(("".join(("".join(a[-2].text.split(","))).split())).split(".")))
    except:
        details["customersReviewsCount"] = "NA"
    return details


def get_lists_of_carousel(carousel, marketPlace):
    lis = carousel.find_elements_by_tag_name("li")
    newli = []
    for x in lis:
        if x.get_attribute("aria-hidden") == "true":
            continue
        try:
            newli.append(scrape_also_bought_element(x, marketPlace))
        except:
            pass
    return newli


def get_also_bought(marketPlace):
    try:
        carousel = driver.find_element_by_id("desktop-dp-sims_purchase-similarities-sims-feature")
        if "alsoBought" in errors.keys():
            errors["alsoBought"] = 0
        return get_lists_of_carousel(carousel, marketPlace)
    except:
        if "alsoBought" in errors.keys():
            errors["alsoBought"] += 1
        else:
            errors["alsoBought"] = 1
        return "NA"

def scrape_and_update(el, marketPlace, mode):
    driver.get(el["htmlLinkPage"])
    print("Scraping " + el["title"][:20])
    temp = {}
    if mode == "amazonDetailedProducts":
        temp["rating"] = get_detailed_ratings()
        temp["customersAlsoBought"] = get_also_bought(marketPlace)
        
    if mode == "amazonSimpleProducts" or mode == "bestSellers":
        temp["ratingOf5Stars"] = get_ratings(marketPlace)
        
    temp["customersReviewsCount"] = get_reviews(marketPlace)
    temp["price"] = get_price(marketPlace)
    temp["currency"] = el["searchParams"][0]["changingInfos"][0]["currency"]
    temp["timestamp"] = timestamp
    for obj in el["searchParams"]:
        obj["changingInfos"].append(temp)
    print("Updating in DB " + el["title"][:20])
    scraperDb[mode].find_one_and_replace({"asinCode": el["asinCode"]}, el)
    return el

def monitorProducts(asins, marketPlace, collection):
    for asin in asins:
        for found in scraperDb[collection].find({"asinCode": asin}):
            scrape_and_update(found, marketPlace, collection)
    return asins


# mem = virtual_memory()
# start = time.time()
# op = monitorProducts(["B078XXN7CP"], "US", "amazonDetailedProducts")
# print("Logging in database")
# end = time.time()
# log = {}

# log["timestamp"] = int(time.time())
# log["scrapingTime"] = int((end-start)*100)/100
# log["objectScraped"] = len(op)
# log["errors"] = errors
# log["type"] = "scrapeAmazon"
# # 1048576  # KB to GB

# log["RAM"] = str(mem.total/1048576*1024) + " GB"
# log["OS"] = platform.linux_distribution()[0]
# log["OSVersion"] = platform.linux_distribution()[1]
# log["CPU"] = {}
# for info in check_output(['lscpu']).decode('utf-8').split('\n'):
#     splitInfo = info.split(':')
#     if splitInfo[0] in ['Architecture', 'CPU op-mode(s)', 'Byte Order', 'CPU(s)', 'Thread(s) per core', 'Core(s) per socket', 'Socket(s)', 'Model name', 'CPU MHz']:
#         try:
#             log["CPU"][splitInfo[0]] = int(splitInfo[1].strip())
#         except:
#             log["CPU"][splitInfo[0]] = splitInfo[1].strip()
# log["ConnectionSpeed"] = {}
# speedCheck = check_output(['speedtest-cli', '--bytes']).decode('utf-8').split('\n'):
# log["ConnectionSpeed"]["Upload"] = speedCheck[-2].split(':')[1].strip()
# log["ConnectionSpeed"]["Download"] = speedCheck[-4].split(':')[1].strip()
# log["ConnectionSpeed"]["Ping"] = speedCheck[-6].split(':')[1].strip()

# scraperDb.executionLog.insert_one(log)