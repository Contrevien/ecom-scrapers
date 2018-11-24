from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
import json
from pymongo import MongoClient
import pyspeedtest
from psutil import virtual_memory
import platform

currencyMap = {
    "US": "USD",
    "IN": "INR",
    "FR": "EUR",
    "IT": "EUR",
    "AU": "AUD"
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

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb
timestamp = int(time.time())
errors = {}

def open_url(marketPlace, keyword, sorter):
    keyword = "+".join(keyword.split())
    url = "http://www.ebay.com/sch/?" + "&_nkw=" + keyword + "&_sop=" + sorter
    driver.get(url)

def process_numbers(value, marketPlace, f):
    if marketPlace == "US" or marketPlace == "AU" or marketPlace == "IN":
        return f("".join(value.split(",")))

def slice_price(value, marketPlace):
    if marketPlace == "US":
        value = value.split("to")[0]
        value = "".join(value.split(","))
        return float(value[1:])

def scrape_element(el, marketPlace, detailedResults):
    obj = dict()
    try:
        obj["htmlLinkPage"] = el.find_element_by_class_name("s-item__link").get_attribute("href")
        obj["uniqueCode"] = int(obj["htmlLinkPage"].split('/')[-1].split('?')[0])
    except:
        obj["htmlLinkPage"] = "NA"
        obj["uniqueCode"] = "NA"
    try:
        obj["title"] = el.find_element_by_class_name("s-item__title").text
    except:
        obj["title"] = "NA"
    try:
        obj["status"] = el.find_element_by_class_name("SECONDARY_INFO").text
    except:
        obj["status"] = "NA"
    obj["changingInfos"] = []
    temp = {}
    if detailedResults != 1:
        try:
            temp["ratingOf5Stars"] = process_numbers(el.find_element_by_class_name("b-starrating__star").text.split()[0], marketPlace, float)
        except:
            temp["ratingOf5Stars"] = "NA"
    try:
        crc = el.find_element_by_class_name("s-item__reviews-count").text
        realCRC = ""
        for n in crc:
            if n.isdigit() or n == " " or n == "," or n == ".":
                realCRC += n
            else:
                break
        temp["customersReviewsCount"] = process_numbers(realCRC, marketPlace, int)
    except:
        temp["customersReviewsCount"] = "NA"
    try:
        temp["price"] = slice_price(el.find_element_by_class_name("s-item__price").text, marketPlace)
    except:
        temp["price"] = "NA"
    obj["changingInfos"].append(temp)
    obj["currency"] = currencyMap[marketPlace]
    return obj

def scrape_less_detailed(marketPlace, limitResults, detailedResults):
    done = False
    resutlsFound = driver.find_element_by_css_selector("h1.srp-controls__count-heading").text
    index = len(resutlsFound) - 1
    while resutlsFound[index] != " ":
        index -= 1
    resutlsFound = process_numbers(resutlsFound[:index], marketPlace, int)
    thisSearch = []
    resutlsScraped = 1
    print("Scraping Page 1 of results")
    while not done:
        try:
            el = driver.find_element_by_id("srp-river-results-listing" + str(resutlsScraped))
            if limitResults == 0 or len(thisSearch) < limitResults:
                thisSearch.append(scrape_element(el, marketPlace, detailedResults))
                resutlsScraped += 1
            else:
                done = True
        except:
            pgn = driver.find_elements_by_class_name("x-pagination__control")[1].get_attribute("href")
            if pgn == "#":
                done = True
            else:
                driver.get(pgn)
                resutlsScraped = 1
    return [thisSearch, resutlsFound]

def get_specs():
    try:
        box = driver.find_element_by_class_name("itemAttr")
        tds = box.find_elements_by_tag_name("td")
        temp = {}
        for i in range(len(tds)):
            if ":" in tds[i].text:
                temp[tds[i].text[:-1]] = tds[i+1].text
        return temp
    except:
        return "NA"

def get_detailed_ratings():
    try:
        temp = {}
        ratings = driver.find_elements_by_css_selector("div.ebay-review-item-r")
        i = 5
        if len(ratings) == 0:
            return "NA"
        for rating in ratings:
            temp[str(i) + "stars"] = int("".join(("".join(("".join(rating.text.split(","))).split())).split(".")))
            i -= 1
        return temp
    except:
        return "NA"

def scrape_detailed(arr, marketPlace):
    for i in range(len(arr)):
        print("Getting details of " + arr[i]["title"][:20])
        driver.get(arr[i]["htmlLinkPage"])
        arr[i]["type"] = "scrapeEbayDetailed"
        arr[i]["description"] = "NA"
        arr[i]["customersAlsoBought"] = "NA"
        arr[i]["productSpecs"] = get_specs()
        arr[i]["searchParams"][0]["changingInfos"][0]["rating"] = get_detailed_ratings()
    return arr


def scrapeEbay(mode, keywords, marketPlaces, sortBy, detailedResults, limitResults):
    finalObject = []
    sortArray = ["12", "1", "10", "15", "16", "7"]
    sorter = sortArray[sortBy]

    for marketPlace in marketPlaces:
        for keyword in keywords:
            print("Searching " + keyword + " in " + marketPlace)

            # open the url
            open_url(marketPlace, keyword, sorter)

            # scrape the results
            thisSearch, totalResults = scrape_less_detailed(marketPlace, limitResults, detailedResults)
            for x in thisSearch:
                x["timestamp"] = timestamp
                x["searchParams"] = []
                temp = {}
                temp["keyword"] = keyword
                temp["marketPlace"] = marketPlace
                temp["sortBy"] = sortBy
                x["changingInfos"][0]["resultsCount"] = totalResults
                x["changingInfos"][0]["timestamp"] = timestamp
                temp["changingInfos"] = x["changingInfos"]
                del x["changingInfos"]
                x["searchParams"].append(temp)
                x["type"] = "scrapeEbaySimple"

            collection = ""
            if detailedResults == 1:
                thisSearch = scrape_detailed(thisSearch, marketPlace)
                collection = "ebayDetailedProducts"
            else:
                collection = "ebaySimpleProducts"
            if mode == 2:
                for x in thisSearch:
                    prev = scraperDb[collection].find({"uniqueCode": x["uniqueCode"]})
                    if prev.count() != 0:
                        for obj in prev:
                            for instance in obj["searchParams"]:
                                if instance["keyword"] == x["searchParams"][0]["keyword"] and instance["limitResults"] == x["searchParams"][0]["limitResults"] and instance["sortBy"] == x["searchParams"][0]["sortBy"] and instance["marketPlace"] == x["searchParams"][0]["marketPlace"]:
                                    print(obj["title"][:20] + " remains Unchanged")
                                    break
                            else:
                                print(obj["title"][:20] + " being updated")
                                obj["searchParams"].append(x["searchParams"][0])
                        scraperDb[collection].find_one_and_replace({"uniqueCode": x["uniqueCode"]}, obj)

                    else:
                        print("Storing in DB " + x["title"][:20])
                        scraperDb[collection].insert_one(x)

            finalObject.append(thisSearch)
    return finalObject

op =scrapeEbay(1, ["sport watch"], ["US"], 0, 1, 200)