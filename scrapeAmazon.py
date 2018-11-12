from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import urllib.request
import time
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

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

finalObject = []
errors = []


def slice_price(price, marketPlace):
    if marketPlace == "US":
        price = price.split()[1:]
        if "," in price[0]:
            price[0] = "".join(price[0].split(","))
        return float(".".join(price))
    elif marketPlace == "FR" or marketPlace == "IT":
        price = price.split()[1:]
        final = ".".join(price[-1].split(","))
        final = "".join(price[:-1]) + final
        return float(final)
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
        return [currency, price]

    except:
        return ["NA", "NA"]


def get_avg_ratings(el):
    try:
        text = el.find_element_by_tag_name(
            "i").get_attribute("class").split()[-1]
        if "a-star" not in text:
            text = el.find_elements_by_tag_name(
                "i")[1].get_attribute("class").split()[-1]
        text = text.split("-")
        rating = ""
        for x in text:
            if x.isdigit():
                rating += x + " "
        return float(".".join(rating.split()))
    except:
        return "NA"


def get_customer_ratings(el):
    try:
        ratings = el.find_elements_by_tag_name("a")[-1].text
        if "," in ratings:
            ratings = "".join(ratings.split(","))
        return int(ratings)
    except:
        return "NA"


def scrape_element(el, marketPlace, timestamp, detailedResults):
    temp = dict()
    temp["asinCode"] = el.get_attribute("data-asin")
    temp["htmlLinkPage"] = el.find_element_by_class_name(
        "s-access-detail-page").get_attribute("href")
    temp["title"] = el.find_element_by_tag_name(
        "h2").get_attribute("data-attribute")
    temp["currency"], price = get_price_and_currency(el, marketPlace)
    temp["prices"] = [{"price": price, "timestamp": timestamp}]
    if detailedResults != 1:
        temp["ratings"] = [{"ratingOf5Stars": get_avg_ratings(el), "timestamp": timestamp}]
    temp["customersReviewsCounts"] = [{"customersReviewsCount": get_customer_ratings(el), "timestamp": timestamp}]

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
                driver.get(driver.find_element_by_id(
                    "pagnNextLink").get_attribute("href"))
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
        return description
    except:
        return "NA"


def get_detailed_ratings(reviewCount):
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
        driver.get(driver.find_element_by_id(
            "softlinesTechnicalSpecificationsLink").get_attribute("href"))
        tbody = driver.find_element_by_id("technicalSpecifications_section_1")
        return filter_specs(tbody)
    except:
        try:
            tbody = driver.find_element_by_id(
                "technicalSpecifications_feature_div")
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
    if marketPlace == "FR" or marketPlace == "IT":
        value = value.split()[1:]
        value = "".join(value)
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
                details["currency"], details["price"] = separate_price_and_currency(
                    span.text, marketPlace)
    except:
        details["currency"], details["price"] = ["NA", "NA"]

    details["htmlLinkPage"] = a[0].get_attribute("href")
    details["ratingOf5stars"] = get_avg_ratings(el)
    try:
        details["customersReviewsCount"] = int(
            "".join(a[-2].text.split(",")))
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
        carousel = driver.find_element_by_id(
            "desktop-dp-sims_purchase-similarities-sims-feature")
        return get_lists_of_carousel(carousel, marketPlace)
    except:
        return "NA"


def get_detailed_results(arr, marketPlace, timestamp):
    for i in range(len(arr)):
        # get detailed versions
        print("Getting details of", arr[i]["title"][:20])
        driver.get(arr[i]["htmlLinkPage"])
        arr[i]["type"] = "scrapeAmazonDetailed"
        arr[i]["ratings"] = [{ "rating": get_detailed_ratings(arr[i]["customersReviewsCounts"][0]["customersReviewsCount"]), "timestamp": timestamp }]
        arr[i]["description"] = get_description()
        arr[i]["customersAlsoBought"] = get_also_bought(marketPlace)
        arr[i]["productSpecs"] = get_specs()
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


def scrapeAmazon(keywords, marketPlaces, sortBy=0, detailedResults=0, limitResults=0):

    sortArray = ["relevancerank", "popularity-rank", "price-asc-rank",
                 "price-desc-rank", "review-rank", "date-desc-rank"]

    sorter = sortArray[sortBy]

    # go to the respective marketPlace
    for marketPlace in marketPlaces:

        # search each keyword
        for keyword in keywords:
            print("Searching " + keyword + " in " + marketPlace)

            # open the url for searching the keyword
            if open_url(marketPlace, keyword, sorter) == -1:
                return

            # save timestamp
            timestamp = int(time.time())

            # scrape the results
            thisSearch, totalResults = scrape_less_detailed(
                marketPlace, limitResults, timestamp, detailedResults)
            for x in thisSearch:
                x["timestamp"] = timestamp
                x["keyword"] = keyword
                x["marketPlace"] = marketPlace
                x["sortBy"] = sortBy
                x["resultsNumber"] = [{"resultsCount": totalResults, "timestamp": timestamp}]
                if limitResults == 0:
                    x["limitResults"] = 0
                else:
                    x["limitResults"] = limitResults
                    thisSearch = thisSearch[:limitResults]
                x["type"] = "scrapeAmazonSimple"

            # if detailedResults
            if detailedResults == 1:
                thisSearch = get_detailed_results(thisSearch, marketPlace, timestamp)

            for x in thisSearch:
                scraperDb.amazonSimpleProducts.insert_one(x)

            # add the result to the final object
            finalObject.extend(thisSearch)

print(finalObject)
scrapeAmazon(["sport watch"], ["US"], 0, 0)

