from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
import json
from pymongo import MongoClient
from psutil import virtual_memory
import platform
from subprocess import check_output

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
    url = ""
    if marketPlace == "US":
        url = "http://www.ebay.com/sch/?" + "&_nkw=" + keyword + "&_sop=" + sorter
    elif marketPlace == "AU":
        url = "http://www.ebay.com.au/sch/?" + "&_nkw=" + keyword + "&_sop=" + sorter
    else:
        url = "http://www.ebay." + marketPlace.lower() + "/sch/?" + "&_nkw=" + keyword + "&_sop=" + sorter
    driver.get(url)

def process_numbers(value, marketPlace, f):
    try:
        if marketPlace == "US" or marketPlace == "AU" or marketPlace == "IN":
            return f("".join(value.split(",")))
        if marketPlace == "FR":
            return f("".join(value.split()))
        if marketPlace == "IT":
            return f("".join(value.split(".")))
    except:
        return "NA"

def slice_price(value, marketPlace):
    if marketPlace == "US":
        value = value.split("to")[0]
        value = value.replace(",", "")
        return float(value[1:])
    if marketPlace == "IT":
        value.replace("EUR", "")
        value = value.replace(" ", "")
        value = value.replace(".", "")
        value = value.replace(",", ".")
        index = 0
        while value[index].isdigit() or value[index] == ".":
            index += 1
        value = value[:index]
        return float(value)
    if marketPlace == "FR":
        value = value.replace(" ", "")
        index = 0
        while value[index].isdigit() or value[index]  == ",":
            index += 1
        value = value[:index]
        value = value.replace(",", ".")
        return float(value)
    if marketPlace == "AU":
        value = value.replace(" ", "")
        value.replace("AU", "")
        value.replace("$", "")
        index = 0
        while value[index].isdigit() or value[index]  == ".":
            index += 1
        value = value[:index]
        return float(value)


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
    temp["currency"] = currencyMap[marketPlace]
    obj["changingInfos"].append(temp)
    return obj

def one_way(marketPlace, limitResults, detailedResults):
    resultsFound = driver.find_element_by_css_selector("h1.srp-controls__count-heading").text
    index = len(resultsFound) - 1
    while resultsFound[index] != " ":
        index -= 1
    resultsFound = process_numbers(resultsFound[:index], marketPlace, int)
    thisSearch = []
    resutlsScraped = 1
    print("Scraping Pages of result")
    done = False
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
    return [thisSearch, resultsFound]

def second_way(marketPlace, limitResults, detailedResults):
    pass

def scrape_less_detailed(marketPlace, limitResults, detailedResults):
    
    try:
        return one_way(marketPlace, limitResults, detailedResults)
    except:
        try:
            return second_way(marketPlace, limitResults, detailedResults)
        except:
            errors["Format Changed"] = 1
            return [-1, -1]
            

def get_specs():
    try:
        box = driver.find_element_by_class_name("itemAttr")
        tds = box.find_elements_by_tag_name("td")
        temp = {}
        for i in range(0, len(tds), 2):
            key = ""
            for ch in tds[i].text[:-1]:
                if ch.isalpha() or ch == " ":
                    key += ch
            
            temp[key] = tds[i+1].text
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
        arr[i]["searchParams"][0]["changingInfos"][0]["customersAlsoBought"] = "NA"
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
                temp["limitResults"] = limitResults
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
                                if instance["keyword"] == x["searchParams"][0]["keyword"] and instance["sortBy"] == x["searchParams"][0]["sortBy"] and instance["marketPlace"] == x["searchParams"][0]["marketPlace"]:
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

mem = virtual_memory()
start = time.time()
op = scrapeEbay(2, ["sport watch"], ["US"], 0, 0, 100)
print("Logging in database")
end = time.time()
# log = {}

# log["timestamp"] = int(time.time())
# log["scrapingTime"] = int((end-start)*100)/100
# log["objectScraped"] = len(op)
# log["errors"] = errors
# log["type"] = "scrapeEbay"
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
# speedCheck = check_output(['speedtest-cli', '--bytes']).decode('utf-8').split('\n')
# log["ConnectionSpeed"]["Upload"] = speedCheck[-2].split(':')[1].strip()
# log["ConnectionSpeed"]["Download"] = speedCheck[-4].split(':')[1].strip()
# log["ConnectionSpeed"]["Ping"] = speedCheck[-6].split(':')[1].strip()

# scraperDb.executionLog.insert_one(log)