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
finalObject = []
errors = {}
deparmentsHistory = ["Base"]


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
    if marketPlace == "IT" or marketPlace == "FR":
        value = value[4:]
        "".join(value.split())
        ".".join(value.split(","))
        return float(value)


def store_data():
    if len(errors) != 0:
        finalObject.insert(0, errors)
    json_data = json.dumps(finalObject)
    with open('test.json', 'w') as f:
        f.write(json_data)
    driver.quit()


def scrape_element(el, marketPlace, limitResults):
    if limitResults != 0 and len(finalObject) == limitResults:
        store_data()
        print("Limit Reached!")
        sys.exit()
    obj = {}
    obj["department"] = deparmentsHistory[1]
    if len(deparmentsHistory) >= 2:
        for i in range(len(deparmentsHistory[2:])):
            obj["sub"*(i+1) + "department"] = deparmentsHistory[i+2]
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

    obj["htmlLinkPage"] = a[0].get_attribute("href")

    try:
        rating = float(a[1].get_attribute("title").split()[0])
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
        crc = int("".join((a[2].text.split(","))))
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

    finalObject.append(obj)


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
        ul = wait.until(EC.presence_of_element_located(
            (By.ID, "zg_browseRoot")))
        print("Going back")
        driver.back()
        deparmentsHistory.pop()
        print("At", deparmentsHistory[-1])


def amazonBestSellers(departments, marketPlaces, limitResults=0):

    for marketPlace in marketPlaces:

        if open_url(marketPlace) == -1:
            return
        print(deparmentsHistory[-1])
        for department in departments.keys():
            loop_and_open(
                department, departments[department], marketPlace, limitResults)
        for x in finalObject:
            x["limitResults"] = limitResults


test = {
    "Amazon Devices & Accessories": {
        "Amazon Devices": {
            "Home Security from Amazon": dict(),
            "Amazon Echo & Alexa Devices": dict(),
            "Dash Buttons": {
                "Baby & Kids": dict(),
                "Beauty": dict(),
                "Beverages": dict(),
            },
        },
        "Amazon Device Accessories": {
            "Adapters & Connectors": dict(),
            "Alexa Gadgets": dict(),
            "Audio": dict(),
        },
    },
    "Computers & Accessories": {
        "Desktops": dict(),
        "Laptops": dict(),
        "Tablets": dict(),
    }
}

amazonBestSellers(test, ["US"], 10)
store_data()
