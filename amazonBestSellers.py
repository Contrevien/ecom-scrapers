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
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("log-level=3")
driver = webdriver.Chrome(options=options, executable_path=ch)
wait = WebDriverWait(driver, 10)

timestamp = int(time.time())
bestSellers = []
errors = {}
deparmentsHistory = ["Base"]

client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def open_url(marketPlace):
    try:
        if marketPlace == "US":
            driver.get("https://www.amazon.com/Best-Sellers/zgbs")
        else:
            driver.get("https://www.amazon." +
                       marketPlace.lower() + "/gp/bestsellers")
        return 1
    except:
        errors["Invalid URL for " + marketPlace] = 1
        return -1


def open_department(department):
    print("Opening", department)
    try:
        ul = wait.until(EC.presence_of_element_located(
            (By.ID, "zg_browseRoot")))
        driver.get(ul.find_element_by_link_text(
            department).get_attribute("href"))
        deparmentsHistory.append(department)
        return 1
    except:
        errors["Cannot open " + department] = 1
        print("Cannot open " + department)
        return -1


def slice_price(value, marketPlace):
    if marketPlace == "US":
        value = value[1:]
        value = "".join(value.split(","))
        return float(value)
    if marketPlace == "IN":
        value = value[2:]
        value = "".join(value.split(","))
        return float(value)
    if marketPlace == "FR":
        price = value.split()[1:]
        final = ".".join(price[-1].split(","))
        final = "".join(price[:-1]) + final
        return float(final)
    if marketPlace == "IT":
        price = value[4:]
        price = "".join(price.split("."))
        price = ".".join(price.split(","))
        return float(price)


def store_data():
    # if len(errors) != 0:
    #     bestSellers.insert(0, errors)
    # json_data = json.dumps(bestSellers)
    # with open('test.json', 'w') as f:
    #     f.write(json_data)
    # driver.quit()
    for x in bestSellers:
        scraperDb.bestSellers.insert_one(x)
    for x in scraperDb.errors.find({"type": "bestSellers"}):
        y = x.copy()
        if len(errors) != 0:
            errors["timestamp"] = timestamp
            y["errors"].append(errors)
            scraperDb.errors.find_one_and_replace({"type": "bestSellers"}, y)


def scrape_element(el, marketPlace, limitResults):
    if limitResults != 0 and len(bestSellers) == limitResults:
        store_data()
        print("Limit Reached!")
        sys.exit()
    obj = {}
    obj["department"] = deparmentsHistory[1]
    try:
        obj["subDepartment"] = deparmentsHistory[2]
    except:
        obj["subDepartment"] = ""
    try:
        obj["subSubDepartment"] = deparmentsHistory[3]
    except:
        obj["subSubDepartment"] = ""
    obj["type"] = "amazonBestSellers"
    obj["marketPlace"] = marketPlace
    obj["timestamp"] = timestamp

    a = el.find_elements_by_class_name("a-link-normal")

    try:
        obj["title"] = a[0].text
        if "title" in errors.keys():
            errors["title"] = 0
    except:
        obj["title"] = "NA"
        if "title" in errors.keys():
            errors["title"] += 1
        else:
            errors["title"] = 1
    try:
        obj["htmlLinkPage"] = a[0].get_attribute("href")
        if "htmlLink" in errors.keys():
            errors["htmlLink"] = 0
    except:
        obj["htmlLinkPage"] = "NA"
        if "htmlLink" in errors.keys():
            errors["htmlLink"] += 1
        else:
            errors["htmlLink"] = 1
    try:
        rating = a[1].get_attribute("title").split()[0]
        if marketPlace == "IT" or marketPlace == "FR":
            rating = float(".".join(rating.split(",")))
        else:
            rating = float(rating)
        if "rating" in errors.keys():
            errors["rating"] = 0
    except:
        rating = "NA"
        if "rating" in errors.keys():
            errors["rating"] += 1
        else:
            errors["rating"] = 1
    obj["ratingsOf5Stars"] = [
        {"timestamp": timestamp, "ratingOf5Stars": rating}]

    try:
        crc = "".join((a[2].text.split(",")))
        crc = "".join(crc.split())
        crc = "".join(crc.split("."))
        crc = int(crc)
        if "crc" in errors.keys():
            errors["crc"] = 0
    except:
        crc = "NA"
        if "crc" in errors.keys():
            errors["crc"] += 1
        else:
            errors["crc"] = 1
    obj["customersReviewsCounts"] = [
        {"timestamp": timestamp, "customersReviewsCount": crc}]

    try:
        price = slice_price(a[3].text, marketPlace)
        if "price" in errors.keys():
            errors["price"] = 0
    except:
        price = "NA"
        if "price" in errors.keys():
            errors["price"] += 1
        else:
            errors["price"] = 1
    obj["currency"] = currencyMap[marketPlace]
    obj["prices"] = [{"timestamp": timestamp, "price": price}]

    bestSellers.append(obj)


def scrape_department(department, marketPlace, limitResults):
    print("Scraping", department)
    ol = wait.until(EC.presence_of_element_located(
        (By.ID, "zg-ordered-list")))
    try:
        nextPage = driver.find_element_by_class_name("a-last")
    except:
        pass
    while True:
        ol = wait.until(EC.presence_of_element_located(
            (By.ID, "zg-ordered-list")))
        for li in ol.find_elements_by_tag_name("li"):
            scrape_element(li, marketPlace, limitResults)
        try:
            nextPage = driver.find_element_by_class_name("a-last")
            if "a-disabled" in nextPage.get_attribute("class"):
                break
            driver.get(nextPage.find_element_by_tag_name(
                "a").get_attribute("href"))
        except:
            break

    while True:
        try:
            pagi = driver.find_element_by_class_name("a-pagination")
            firstLi = pagi.find_element_by_tag_name("li")
            if "a-disabled" in firstLi.get_attribute("class"):
                break
            driver.back()
            wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "a-last")))
        except:
            break
    print("Going back")
    driver.back()
    deparmentsHistory.pop()
    print("At", deparmentsHistory[-1])


def loop_and_open(department, value, marketPlace, limitResults):
    if open_department(department) == -1:
        return
    if len(value) == 0:
        scrape_department(department, marketPlace, limitResults)
    else:
        for subdep in value.keys():
            loop_and_open(subdep, value[subdep], marketPlace, limitResults)
        wait.until(EC.presence_of_element_located(
            (By.ID, "zg_browseRoot")))
        print("Going back")
        driver.back()
        deparmentsHistory.pop()
        print("At", deparmentsHistory[-1])


def amazonBestSellers(departments, marketPlaces, limitResults=0, mode=1):

    for marketPlace in marketPlaces:
        if open_url(marketPlace) == -1:
            return
        print(deparmentsHistory[-1])
        for department in departments.keys():
            loop_and_open(
                department, departments[department], marketPlace, limitResults)
        for x in bestSellers:
            x["limitResults"] = limitResults
    if mode == 1:
        store_data()
    else:
        for x in scraperDb.errors.find({"type": "bestSellers"}):
            y = x.copy()
            if len(errors) != 0:
                errors["timestamp"] = timestamp
                y["errors"].append(errors)
                scraperDb.errors.find_one_and_replace(
                    {"type": "bestSellers"}, y)
        return bestSellers
    driver.quit()


test = {
    "Computers & Accessories": {
        "Desktops": dict(),
    },
    "Amazon Devices & Accessories": {
        "Amazon Devices": {
            "Home Security from Amazon": dict(),
        },
    },
}
