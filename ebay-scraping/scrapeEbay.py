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
    temp = dict()
    temp["htmlLinkPage"] = el.find_element_by_class_name("s-item__link").get_attribute("href")
    temp["title"] = el.find_element_by_class_name("s-item__title").text
    temp["status"] = el.find_element_by_class_name("SECONDARY_INFO").text
    if detailedResults != 1:
        temp["ratingsOf5Stars"] = [{"ratingOf5Stars": process_numbers(el.find_element_by_class_name("b-starrating__star").text.split()[0], marketPlace, float), "timestamp": timestamp}]
    crc = el.find_element_by_class_name("s-item__reviews-count").text
    realCRC = ""
    for n in crc:
        if n.isdigit() or n == " " or n == "," or n == ".":
            realCRC += n
        else:
            break
    temp["customersReviewsCounts"] = [{"customersReviewsCount": process_numbers(realCRC, marketPlace, int), "timestamp": timestamp}]
    temp["price"] = slice_price(el.find_element_by_class_name("s-item__price").text, marketPlace)
    temp["currency"] = currencyMap[marketPlace]
    return temp

def scrape_less_detailed(marketPlace, limitResults, detailedResults):
    done = False
    resutlsFound = driver.find_element_by_css_selector("h1.srp-controls__count-heading").text
    index = len(resutlsFound) - 1
    while resutlsFound[index] != " ":
        index -= 1
    resutlsFound = process_numbers(resutlsFound[:index], marketPlace, int)
    page = 1
    thisSearch = []
    resutlsScraped = 1
    print("Scraping Page 1 of results")
    while not done:
        try:
            el = driver.find_element_by_id("srp-river-results-listing" + str(resutlsScraped))
            if limitResults == 0 or len(thisSearch) < limitResults:
                thisSearch.append(scrape_element(el, marketPlace, detailedResults))
            resutlsScraped += 1
        except:
            pgn = driver.find_elements_by_class_name("x-pagination__control")[1].get_attribute("href")
            if pgn == "#":
                done = True
            else:
                driver.get(pgn)
                resutlsScraped = 1
    return [thisSearch, resutlsFound]

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
                x["keyword"] = keyword
                x["marketPlace"] = marketPlace
                x["sortBy"] = sortBy
                x["resultsNumber"] = [{"resultsCount": totalResults, "timestamp": timestamp}]
                