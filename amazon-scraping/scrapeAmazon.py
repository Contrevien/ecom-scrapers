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
options.set_headless(headless=True)
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("log-level=3")
try:
    driver = webdriver.Chrome(options=options, executable_path=ch)
except:
    try:
        os.chdir('..')
        ch = os.getcwd() + '/tools/chromedriver'
        os.chdir('amazon-scraping')
        driver = webdriver.Chrome(options=options, executable_path=ch)
    except:
        print("Install chromedriver!")
wait = WebDriverWait(driver, 10)

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb
timestamp = int(time.time())
errors = {}


def slice_price(price, marketPlace):
    if marketPlace == "US":
        price = price.split()[1:]
        if "," in price[0]:
            price[0] = "".join(price[0].split(","))
        return float(".".join(price))
    elif marketPlace == "FR":
        price = price.split()[1:]
        final = ".".join(price[-1].split(","))
        final = "".join(price[:-1]) + final
        return float(final)
    elif marketPlace == "IT":
        price = price[4:]
        price = "".join(price.split("."))
        price = ".".join(price.split(","))
        return float(price)
    elif marketPlace == "IN":
        price = price.strip()
        if "," in price:
            price = "".join(price.split(","))
        return float(price)


def get_price_and_currency(el, marketPlace):
    try:
        currency = currencyMap[marketPlace]
        a = el.find_elements_by_class_name("a-link-normal")
        price = ""
        if len(a) == 5:
            price = a[-1].text.strip()
        elif len(a) == 6:
            price = a[-2].text.strip()
        elif len(a) == 7:
            price = a[-3].text.strip()
        elif len(a) == 4:
            price = a[-2].text.strip()
        else:
            return ["NA", "NA"]
        price = slice_price(price, marketPlace)
        if "price" in errors.keys():
            errors["price"] = 0
        return [currency, price]
    except:
        if "price" in errors.keys():
            errors["price"] += 1
        else:
            errors["price"] = 1
        return ["NA", "NA"]


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


def get_customer_ratings(el, marketPlace):
    try:
        ratings = el.find_elements_by_tag_name("a")[-1].text
        if marketPlace == "US" or marketPlace == "IN":
            ratings = "".join(ratings.split(","))
        if marketPlace == "FR":
            ratings = "".join(ratings.split())
        if marketPlace == "IT":
            ratings = "".join(ratings.split("."))
        if "crc" in errors.keys():
            errors["crc"] = 0
        return int(ratings)
    except:
        if "crc" in errors.keys():
            errors["crc"] += 1
        else:
            errors["crc"] = 1
        return "NA"


def scrape_element(el, marketPlace, timestamp, detailedResults):
    temp = dict()
    temp["asinCode"] = el.get_attribute("data-asin")
    temp["htmlLinkPage"] = el.find_element_by_class_name("s-access-detail-page").get_attribute("href")
    temp["title"] = el.find_element_by_tag_name("h2").get_attribute("data-attribute")
    temp["changingInfos"] = []
    temptemp = dict()
    temptemp["timestamp"] = timestamp
    temp["changingInfos"].append(temptemp)
    temp["changingInfos"][0]["currency"], temp["changingInfos"][0]["price"] = get_price_and_currency(el, marketPlace)
    if detailedResults != 1:
        temp["changingInfos"][0]["ratingOf5Stars"] = get_avg_ratings(el)
    temp["changingInfos"][0]["customersReviewsCount"] = get_customer_ratings(el, marketPlace)
    return temp
    


def scrape_less_detailed(marketPlace, limitResults, timestamp, detailedResults):
    done = False
    resultsFound = 0
    page = 1
    thisSearch = []
    print("Scraping Page 1 of results")
    while not done:
        try:
            el = driver.find_element_by_id("result_" + str(resultsFound))
            if limitResults == 0 or resultsFound < limitResults:
                thisSearch.append(scrape_element(el, marketPlace, timestamp, detailedResults))
            resultsFound += 1
        except:
            try:
                driver.get(driver.find_element_by_id("pagnNextLink").get_attribute("href"))
                page += 1
                print("Scraping Page " + str(page) + " of results")
            except:
                done = True
    return [thisSearch, resultsFound]


def get_description():
    try:
        des_div = driver.find_element_by_id("feature-bullets")
        des_spans = des_div.find_elements_by_class_name("a-list-item")
        description = []
        for des in des_spans:
            description.append(des.text)
        description = "".join(description)
        if "description" in errors.keys():
            errors["description"] = 0
        return description
    except:
        if "description" in errors.keys():
            errors["description"] += 1
        else:
            errors["description"] = 1
        return "NA"


def get_detailed_ratings():
    try:
        review = wait.until(EC.presence_of_element_located((By.ID, "reviewsMedley")))
        table = review.find_element_by_id("histogramTable")
        percents = table.find_elements_by_class_name("a-text-right")
        review_arr = []
        for i in percents:
            review_arr.append(int(i.text[:-1]))
        ratings = dict()
        for i in range(5):
            ratings[str(5-i)+"stars"] = review_arr[i]
        if "detailed-ratings" in errors.keys():
            errors["detailed-ratings"] = 0
        return ratings
    except:
        if "detailed-ratings" in errors.keys():
            errors["detailed-ratings"] += 1
        else:
            errors["detailed-ratings"] = 1
        return "NA"


def filter_specs(tbody):
    heads = tbody.find_elements_by_tag_name("th")
    values = tbody.find_elements_by_tag_name("td")
    productSpecs = dict()
    for i in range(len(heads)):
        productSpecs[heads[i].text.strip()] = values[i].text.strip()
    return productSpecs


def get_specs():
    tbody = ""
    try:
        driver.get(driver.find_element_by_id("softlinesTechnicalSpecificationsLink").get_attribute("href"))
        tbody = driver.find_element_by_id("technicalSpecifications_section_1")
        return filter_specs(tbody)
    except:
        try:
            tbody = driver.find_element_by_id("technicalSpecifications_feature_div")
            return filter_specs(tbody)
        except:
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


def get_detailed_results(arr, marketPlace, timestamp):
    for i in range(len(arr)):
        # get detailed versions
        print("Getting details of " + arr[i]["title"][:20])
        driver.get(arr[i]["htmlLinkPage"])
        arr[i]["type"] = "scrapeAmazonDetailed"
        arr[i]["description"] = get_description()
        arr[i]["searchParams"][0]["changingInfos"][0]["customersAlsoBought"] = get_also_bought(marketPlace)
        arr[i]["productSpecs"] = get_specs()
        arr[i]["searchParams"][0]["changingInfos"][0]["rating"] = get_detailed_ratings()
    return arr


def open_url(marketPlace, keyword, sorter):
    try:
        keyword = "+".join(keyword.split())
        if marketPlace == "US":
            driver.get(
                "https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=" + keyword + "&sort=" + sorter)
        else:
            driver.get("https://www.amazon." + marketPlace.lower() +
                       "/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=" + keyword + "&sort=" + sorter)
        return 1
    except:
        return -1


def scrapeAmazon(mode, keywords, marketPlaces, sortBy, detailedResults=0, limitResults=0):
    finalObject = []
    sortArray = [
        "relevancerank",
        "price-asc-rank",
        "price-desc-rank",
        "review-rank",
        "date-desc-rank"
    ]

    sorter = sortArray[sortBy]

    # go to the respective marketPlace
    for marketPlace in marketPlaces:

        # search each keyword
        for keyword in keywords:
            print("Searching " + keyword + " in " + marketPlace)

            # open the url for searching the keyword
            if open_url(marketPlace, keyword, sorter) == -1:
                return

            # scrape the results
            thisSearch, totalResults = scrape_less_detailed(marketPlace, limitResults, timestamp, detailedResults)
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
                if limitResults == 0:
                    temp["limitResults"] = 0
                else:
                    temp["limitResults"] = limitResults
                    thisSearch = thisSearch[:limitResults]
                x["type"] = "scrapeAmazonSimple"

            collection = ""
            # if detailedResults
            if detailedResults == 1:
                thisSearch = get_detailed_results(thisSearch, marketPlace, timestamp)
                collection = "amazonDetailedProducts"
            else:
                collection = "amazonSimpleProducts"
            if mode == 2:
                for x in thisSearch:
                    prev = scraperDb[collection].find({"asinCode": x["asinCode"]})
                    if prev.count() != 0:
                        for obj in prev:
                            for instance in obj["searchParams"]:
                                if instance["keyword"] == x["searchParams"][0]["keyword"] and instance["limitResults"] == x["searchParams"][0]["limitResults"] and instance["sortBy"] == x["searchParams"][0]["sortBy"] and instance["marketPlace"] == x["searchParams"][0]["marketPlace"]:
                                    print(obj["title"][:20] + " remains Unchanged")
                                    break
                            else:
                                print(obj["title"][:20] + " being updated")
                                obj["searchParams"].append(x["searchParams"][0])
                        scraperDb[collection].find_one_and_replace({"asinCode": x["asinCode"]}, obj)

                    else:
                        print("Storing in DB " + x["title"][:20])
                        scraperDb[collection].insert_one(x)
            # add the result to the final object
            finalObject.extend(thisSearch)
    driver.quit()
    return finalObject

mem = virtual_memory()
start = time.time()
op = scrapeAmazon(1, ["32gb memory usb"], ["US"], 0, 0, 0)
print("Creating log in database")
end = time.time()
log = {}

log["timestamp"] = int(time.time())
log["scrapingTime"] = int((end-start)*100)/100
log["objectScraped"] = len(op)
log["errors"] = errors
log["type"] = "scrapeAmazon"
# 1048576  # KB to GB

log["RAM"] = str(mem.total/1048576*1024) + " GB"
log["OS"] = platform.linux_distribution()[0]
log["OSVersion"] = platform.linux_distribution()[1]
log["CPU"] = {}
for info in check_output(['lscpu']).decode('utf-8').split('\n'):
    splitInfo = info.split(':')
    if splitInfo[0] in ['Architecture', 'CPU op-mode(s)', 'Byte Order', 'CPU(s)', 'Thread(s) per core', 'Core(s) per socket', 'Socket(s)', 'Model name', 'CPU MHz']:
        try:
            log["CPU"][splitInfo[0]] = int(splitInfo[1].strip())
        except:
            log["CPU"][splitInfo[0]] = splitInfo[1].strip()
log["ConnectionSpeed"] = {}
speedCheck = check_output(['speedtest-cli', '--bytes']).decode('utf-8').split('\n')
log["ConnectionSpeed"]["Upload"] = speedCheck[-2].split(':')[1].strip()
log["ConnectionSpeed"]["Download"] = speedCheck[-4].split(':')[1].strip()
log["ConnectionSpeed"]["Ping"] = speedCheck[-6].split(':')[1].strip()

scraperDb.executionLog.insert_one(log)
