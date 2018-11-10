from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import urllib.request
import time
import json

ch = os.getcwd() + '/tools/chromedriver'
options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("log-level=3")
driver = webdriver.Chrome(options=options, executable_path=ch)
wait = WebDriverWait(driver, 600)
finalObject = []
matchWord = []
errors = []


def change_match_word_as_per_marketPlace(marketplace):
    if marketplace == "US" or marketplace == "IN":
        matchWord.append("Customers who bought this item also bought")
        matchWord.append("Customers also shopped for")
    if marketplace == "FR":
        matchWord.append(
            "Les clients ayant acheté cet article ont également acheté")


def go_to_marketPlace(marketPlace):
    '''Switch to the respective marketplace'''
    print("Loading website for", marketPlace)
    if marketPlace == "US":
        driver.get("https://www.amazon.com/")
    else:
        driver.get("https://www.amazon.com" + marketPlace.lower() + "/")
    change_match_word_as_per_marketPlace(marketPlace)


def search(keyword):
    try:
        searchBar = wait.until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        searchBar.send_keys(keyword + "\n")
        return 1
    except Exception as e:
        print(e)
        errors.append(e)
        return -1


def get_price_and_currency(el):
    try:
        currency = el.find_element_by_class_name("sx-price-currency").text
        if currency == "$":
            currency = "USD"
        whole = el.find_element_by_class_name("sx-price-whole").text
        fractional = el.find_element_by_class_name("sx-price-fractional").text
        return [currency, float(whole + "." + fractional)]
    except:
        return ["NA", "NA"]


def get_avg_ratings(el):
    try:
        text = el.find_element_by_tag_name(
            "i").get_attribute("class").split()[-1]
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


def scrape_element(el):
    temp = dict()
    temp["asinCode"] = el.get_attribute("data-asin")
    temp["htmlLinkPage"] = el.find_element_by_class_name(
        "s-access-detail-page").get_attribute("href")
    temp["title"] = el.find_element_by_tag_name(
        "h2").get_attribute("data-attribute")
    temp["currency"], temp["price"] = get_price_and_currency(el)
    temp["ratingOf5stars"] = get_avg_ratings(el)
    temp["customersReviewsCount"] = get_customer_ratings(el)
    return temp


def scrape_less_detailed():
    done = False
    resultsFound = 0
    page = 1
    thisSearch = []
    print("Scraping Page 1 of results")
    while not done:
        try:
            el = driver.find_element_by_id("result_" + str(resultsFound))
            thisSearch.append(scrape_element(el))
            resultsFound += 1
        except:
            try:
                driver.get(driver.find_element_by_id(
                    "pagnNextLink").get_attribute("href"))
                page += 1
                print("Scraping Page " + str(page) + " of results")
            except:
                done = True
    return thisSearch


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
            per = int(i.text[:-1])
            review_arr.append(int(reviewCount*(per/100)))
        ratings = dict()
        for i in range(5):
            ratings[str(5-i)+"stars"] = review_arr[i]
        return ratings
    except:
        return "NA"


def get_specs():
    productSpecs = dict()
    try:
        driver.find_element_by_id(
            "softlinesTechnicalSpecificationsLink").click()
        tbody = driver.find_element_by_id("technicalSpecifications_section_1")
        heads = tbody.find_elements_by_tag_name("th")
        values = tbody.find_elements_by_tag_name("td")

        for i in range(len(heads)):
            productSpecs[heads[i].text.strip()] = values[i].text.strip()
        return productSpecs
    except:
        return "NA"


def scrape_also_bought_element(el):
    details = dict()
    dets = el.text.split("\n")
    details["title"] = dets[0]
    return details


def get_also_bought():
    try:
        carousel = driver.find_element_by_id(
            "desktop-dp-sims_purchase-similarities-sims-feature")
        lis = carousel.find_elements_by_tag_name("li")
        for i in range(len(lis)):
            if lis[i].get_attribute("aria-hidden") == "true":
                continue
            lis[i] = scrape_also_bought_element(lis[i])
        return lis
    except:
        return "NA"


def get_detailed_results(arr):
    for i in range(len(arr)):
        # get description
        driver.get(arr[i]["htmlLinkPage"])
        arr[i]["type"] = "scrapeAmazonDetailed"
        arr[i]["rating"] = get_detailed_ratings(
            arr[i]["customersReviewsCount"])
        arr[i]["description"] = get_description()
        arr[i]["customersAlsoBought"] = get_also_bought()
        arr[i]["productSpecs"] = get_specs()
    return arr


def scrapeAmazon(keywords, marketPlaces, sortBy=0, detailedResults=0, limitResults=-1):

    # go to the respective marketPlace
    for marketPlace in marketPlaces:
        go_to_marketPlace(marketPlace)

        # search each keyword
        for keyword in keywords:
            print("Searching " + keyword + " in " + marketPlace)

            # find the search bar and enter the keyword
            if search(keyword) == -1:
                return

            # save timestamp
            timestamp = int(time.time())

            # scrape the results
            thisSearch = scrape_less_detailed()
            for x in thisSearch:
                x["timestamp"] = timestamp
                x["keyword"] = keyword
                x["marketPlace"] = marketPlace
                x["sortBy"] = sortBy
                x["resultsNumber"] = len(thisSearch)
                if limitResults == -1:
                    x["limitResults"] = "no limit"
                else:
                    x["limitResults"] = limitResults
                x["type"] = "scrapeAmazonSimple"

            if limitResults != -1:
                thisSearch = thisSearch[:limitResults]

            # if detailedResults
            if detailedResults == 1:
                thisSearch = get_detailed_results(thisSearch)

            # add the result to the final object
            finalObject.extend(thisSearch)


dummy = [
    {
        "htmlLinkPage": "https://www.amazon.com/Timex-TW5M03400-Ironman-Classic-Full-Size/dp/B01F8V3T1C/ref=sr_1_35?ie=UTF8&qid=1541837706&sr=8-35&keywords=sport+watch",
        "customersReviewsCount": 50
    }
]

get_detailed_results(dummy)
js = json.dumps(finalObject)
with open('result.json', 'w') as fp:
    fp.write(js)
