from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
import json
from pymongo import MongoClient
import platform
from psutil import virtual_memory
from subprocess import check_output

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
# options.set_headless(headless=True)
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
    keyword = keyword.replace(" ", "+")
    url = 'https://www.alibaba.com/showroom/{0}.html'.format(keyword)
    driver.get(url)
    if sorter == 1:
        driver.get(driver.find_element_by_id("TRALV").get_attribute("href"))
    if sorter == 2:
        driver.get(driver.find_element_by_id("RESRAT").get_attribute("href"))

def slice_price(value, marketPlace):
    if marketPlace == "US":
        value = value.replace("US", "")
        value = value.replace(",", "")
        value = value.replace(" ", "")
        value = value.replace("$", "")
        dash = value.find("-")
        if dash != -1:
            value = value[:dash]
        return float(value)

def scrape_element(el, marketPlace, detailedResults):
    obj = dict()

    try:
        head = el.find_element_by_class_name("title")
        obj["htmlLinkPage"] = head.find_element_by_tag_name("a").get_attribute("href")
        obj["uniqueCode"] = int(obj["htmlLinkPage"].split('?')[0].split('_')[-1][:-5])
        obj["title"] = head.find_element_by_tag_name("a").text
    except:
        obj["htmlLinkPage"] = "NA"
        obj["uniqueCode"] = "NA"
        obj["title"] = "NA"
    
    
    obj["changingInfos"] = []
    temp = {}
    
    try:
        temp["ratingOf5Stars"] = float(el.find_element_by_class_name("star").get_attribute("title").split()[0].replace(",", "."))
    except:
        temp["ratingOf5Stars"] = "NA"
    
    try:
        crc = el.find_element_by_class_name("ratingCount").get_attribute("title")
        realCRC = ""
        for n in crc:
            if n.isdigit() or n == " " or n == "," or n == ".":
                realCRC += n
            else:
                break
        realCRC = realCRC.replace(",", "")
        realCRC = realCRC.replace(".", "")
        realCRC = realCRC.replace(" ", "")
        temp["customersReviewsCount"] = int(realCRC)
    except:
        temp["customersReviewsCount"] = "NA"
    
    try:
        priceEl = el.find_element_by_class_name("price")
        temp["price"] = slice_price(priceEl.find_element_by_tag_name("b").text, marketPlace)
    except:
        temp["price"] = "NA"
    
    try:
        minOr = el.find_element_by_class_name("min-order")
        minOr = minOr.find_element_by_tag_name("b").text
        realOne = ""
        for n in minOr:
            if n.isdigit() or n == " " or n == "," or n == ".":
                realOne += n
            else:
                break
        realOne = realOne.replace(",", "")
        realOne = realOne.replace(".", "")
        realOne = realOne.replace(" ", "")
        temp["minOrder"] = int(realOne)
    except:
        temp["minOrder"] = "NA"

    temp["currency"] = currencyMap[marketPlace]
    obj["changingInfos"].append(temp)
    return obj
        

def scrape_less_detailed(marketPlace, limitResults, detailedResults):
    done = False
    resultsFound = ""
    try:
        resultsFound = driver.find_element_by_css_selector("div.selected-total-wrap").text.split()[0]
    except:
        try:
            resultsFound = driver.find_element_by_css_selector("span.rcnt").text
        except:
            resultsFound = "NA"
    resultsFound = int(resultsFound.replace(",", ""))
    thisSearch = []

    print("Scraping Pages of result")
    while not done:
        try:
            els = driver.find_elements_by_class_name("m-gallery-product-item-wrap")
            for el in els:
                if limitResults == 0 or len(thisSearch) < limitResults:
                    thisSearch.append(scrape_element(el, marketPlace, detailedResults))
                else:
                    done = True
                    break
            else:
                driver.execute_script('document.getElementsByClassName("next")[0].click();')
        except:
            done = True
    return [thisSearch, resultsFound]


def get_specs():
    temp = {}
    flag = True
    prev = ""
    try:
        for x in driver.find_element_by_class_name("do-entry-list").text.split("\n"):
            x = x.strip()
            if x == "":
                continue
            if flag:
                key = ""
                for ch in x:
                    if ch.isalnum() or ch == " ":
                        key += ch
                temp[key] = ""
                prev = key
                flag = False
            else:
                flag = True
                temp[prev] = x
        return temp
    except:
        return "NA"

def get_you_may_like(marketPlace):
    try:
        extras = []
        for el in driver.find_elements_by_class_name("info"):
            temp = {}
            try:
                temp["title"] = el.find_element_by_class_name("esite-link-normal").text
                temp["htmlLinkPage"] = el.find_element_by_class_name("esite-link-normal").get_attribute("href")
            except:
                continue
            try:
                temp["price"] = slice_price(el.find_element_by_class_name("num").text, marketPlace)
                temp["currency"] = currencyMap[marketPlace]
            except:
                temp["price"] = "NA"
                temp["currency"] = "NA"
            try:
                minOr = el.find_element_by_tag_name("moq").text
                realOne = ""
                for n in minOr:
                    if n.isdigit() or n == " " or n == "," or n == ".":
                        realOne += n
                    else:
                        break
                realOne = realOne.replace(",", "")
                realOne = realOne.replace(".", "")
                realOne = realOne.replace(" ", "")
                temp["minOrder"] = int(realOne)
            except:
                temp["minOrder"] = "NA"
            extras.append(temp)
        return extras
    except:
        return "NA"

def get_detailed_results(arr, marketPlace):
    for i in range(len(arr)):
        print("Getting details of " + arr[i]["title"][:20])
        driver.get(arr[i]["htmlLinkPage"])
        arr[i]["type"] = "scrapeAlibabaDetailed"
        arr[i]["searchParams"][0]["changingInfos"][0]["youMayLike"] = get_you_may_like(marketPlace)
        arr[i]["productSpecs"] = get_specs()
    return arr

def scrapeAlibaba(mode, keywords, marketPlaces, sortBy, detailedResults, limitResults=0):
    finalObject = []

    for marketPlace in marketPlaces:
        for keyword in keywords:
            print("Searching " + keyword + " in " + marketPlace)

            # open the url for searching the keyword
            if open_url(marketPlace, keyword, sortBy) == -1:
                return

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
                temp["changingInfos"] = x["changingInfos"]
                del x["changingInfos"]
                x["searchParams"].append(temp)
                temp["limitResults"] = limitResults
                x["type"] = "scrapeAlibabaSimple"

            collection = ""
            # if detailedResults
            if detailedResults == 1:
                thisSearch = get_detailed_results(thisSearch, marketPlace)
                collection = "alibabaDetailedProducts"
            else:
                collection = "alibabaSimpleProducts"
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
            # add the result to the final object
            finalObject.extend(thisSearch)
    return finalObject

# mem = virtual_memory()
# start = time.time()
# op = scrapeAlibaba(2, ["sport watch"], ["US"], 1, 1, 2)
# print("Logging in database")
# end = time.time()
# log = {}

# log["timestamp"] = int(time.time())
# log["scrapingTime"] = int((end-start)*100)/100
# log["objectScraped"] = len(op)
# log["errors"] = errors
# log["type"] = "scrapeAlibaba"
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