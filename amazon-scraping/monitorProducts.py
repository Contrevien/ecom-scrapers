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
# from scrapeAmazon import get_detailed_ratings


ch = os.getcwd() + '/tools/chromedriver'
options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
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


def scrape_and_update(el, mode):
    driver.get(el["htmlLinkPage"])
    wait.until(EC.presence_of_element_located((By.ID, "reviewsMedley")))
    newOne = el.copy()
    if mode == "detailed":
        rating = get_detailed_ratings()
        if newOne["ratings"][-1]["rating"] != rating:
            newOne["ratings"].append(
                {"timestamp": timestamp, "rating": rating})
        else:
            newOne["ratings"][-1]["timestamp"] = timestamp
    if mode == "simple" or mode == "best":
        rating = get_ratings(el["marketPlace"])
        if newOne["ratingsOf5Stars"][-1]["ratingOf5Stars"] != rating:
            newOne["ratingsOf5Stars"].append(
                {"timestamp": timestamp, "ratingOf5Stars": rating})
        else:
            newOne["ratingsOf5Stars"][-1]["timestamp"] = timestamp
    crc = get_reviews(el["marketPlace"])
    if newOne["customersReviewsCounts"][-1]["customersReviewsCount"] != crc:
        newOne["customersReviewsCounts"].append(
            {"timestamp": timestamp, "customersReviewsCount": crc})
    else:
        newOne["customersReviewsCounts"][-1]["timestamp"] = timestamp
    price = get_price(el["marketPlace"])
    if newOne["prices"][-1]["price"] != price:
        newOne["prices"].append(
            {"timestamp": timestamp, "price": price})
    else:
        newOne["prices"][-1]["timestamp"] = timestamp
    return newOne


def monitor_best_sellers():
    for x in scraperDb.bestSellers.find({"type": "amazonBestSellers"}):
        print("Scraping", x["title"][:20])
        temp = scrape_and_update(x, "best")
        print("Updating", x["title"][:20])
        scraperDb.bestSellers.find_one_and_replace(
            {"_id": x["_id"]}, temp)


def monitor_simple_products():
    for x in scraperDb.amazonSimpleProducts.find({"type": "scrapeAmazonSimple"}):
        print("Scraping", x["title"][:20])
        temp = scrape_and_update(x, "simple")
        print("Updating", x["title"][:20])
        scraperDb.amazonSimpleProducts.find_one_and_replace(
            {"_id": x["_id"]}, temp)


def monitor_detailed_products():
    for x in scraperDb.amazonDetailedProducts.find({"type": "scrapeAmazonDetailed"}):
        print("Scraping", x["title"][:20])
        temp = scrape_and_update(x, "detailed")
        print("Updating", x["title"][:20])
        scraperDb.amazonDetailedProducts.find_one_and_replace(
            {"_id": x["_id"]}, temp)


def monitorProducts():
    monitor_detailed_products()
    monitor_simple_products()
    monitor_best_sellers()
