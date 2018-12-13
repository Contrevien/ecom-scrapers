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
import sys

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
        ul = wait.until(EC.presence_of_element_located((By.ID, "zg_browseRoot")))
        driver.get(ul.find_element_by_link_text(department).get_attribute("href"))
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


def scrape_detailed(d):
    print("Getting details of " + d["title"][:20])
    
    try:
        seller = driver.find_element_by_id("merchant-info")
        d["seller"] = seller.find_element_by_tag_name("a").text
    except:
        try:
            seller = driver.find_element_by_id("usedbuyBox")
            for row in seller.find_elements_by_class_name("a-row"):
                if "Sold by" in row.text:
                    d["seller"] = row.find_element_by_tag_name("a").text
                    break
            else:
                d["seller"] = "NA"
        except:
            d["seller"] = "NA"
    
    container = ""
    try:
        container = driver.find_element_by_id("productDetails_detailBullets_sections1")
    except:
        link = d["htmlLinkPage"]
        try:
            d["asinCode"] = link.split("/")[-2]
        except:
            d["asinCode"] = "NA"
        d["bestSellersRank"] = "NA"
        return d
    for tr in container.find_elements_by_tag_name("tr"):
        if tr.find_element_by_tag_name("th").text.strip() == "ASIN":
            d["asinCode"] = tr.find_element_by_tag_name("td").text
        if tr.find_element_by_tag_name("th").text.strip() == "Best Sellers Rank":
            rank = tr.find_element_by_tag_name("td").text
            final = ""
            for ch in rank:
                if ch.isalpha():
                    break
                final += ch
            final = final.replace("#", "")
            final = final.replace(" ", "")
            final = final.replace(",", "")
            final = final.replace(".", "")
            try:
                d["bestSellersRank"] = int(final)
            except:
                d["bestSellersRank"] = "NA"
    return d


def scrape_element(el, marketPlace, limitResults):
    if limitResults != 0 and len(bestSellers) == limitResults:
        for x in bestSellers:
            x["limitResults"] = limitResults
            driver.get(x["htmlLinkPage"])
            x = scrape_detailed(x)
        # print(bestSellers)
        store_data()
        sys.exit()
    obj = {}
    obj["levels"] = []
    for i in range(1,len(deparmentsHistory)):
        obj["levels"].append(deparmentsHistory[i])
    obj["numberOfLevels"] = len(obj["levels"])
    obj["type"] = "amazonBestSellers"
    obj["marketPlace"] = marketPlace
    obj["timestamp"] = timestamp
    obj["changingInfos"] = []
    temp = {}
    temp["timestamp"] = timestamp
    obj["changingInfos"].append(temp)

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
    obj["changingInfos"][0]["ratingOf5Stars"] = rating

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
    obj["changingInfos"][0]["customersReviewsCount"] = crc

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
    obj["changingInfos"][0]["currency"] = currencyMap[marketPlace]
    obj["changingInfos"][0]["price"] = price

    bestSellers.append(obj)


def scrape_department(department, marketPlace, limitResults):
    print("Scraping", department)
    ol = wait.until(EC.presence_of_element_located((By.ID, "zg-ordered-list")))
    try:
        nextPage = driver.find_element_by_class_name("a-last")
    except:
        pass
    while True:
        ol = wait.until(EC.presence_of_element_located((By.ID, "zg-ordered-list")))
        for li in ol.find_elements_by_tag_name("li"):
            scrape_element(li, marketPlace, limitResults)
        try:
            nextPage = driver.find_element_by_class_name("a-last")
            if "a-disabled" in nextPage.get_attribute("class"):
                break
            driver.get(nextPage.find_element_by_tag_name("a").get_attribute("href"))
        except:
            break

    while True:
        try:
            pagi = driver.find_element_by_class_name("a-pagination")
            firstLi = pagi.find_element_by_tag_name("li")
            if "a-disabled" in firstLi.get_attribute("class"):
                break
            driver.back()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "a-last")))
        except:
            break
    deparmentsHistory.pop()


# def loop_and_open(department, value, marketPlace, limitResults):
#     if open_department(department) == -1:
#         return
#     if len(value) == 0:
#         scrape_department(department, marketPlace, limitResults)
#     else:
#         for subdep in value.keys():
#             loop_and_open(subdep, value[subdep], marketPlace, limitResults)
#         wait.until(EC.presence_of_element_located((By.ID, "zg_browseRoot")))
#         print("Going back")
#         driver.back()
#         deparmentsHistory.pop()
#         print("At", deparmentsHistory[-1])


def loop_and_open(department, marketPlace, limitResults, levels=0):
    ul = wait.until(EC.presence_of_element_located((By.ID, "zg_browseRoot")))
    done = False
    l = 1
    while not done:
        try:
            ul = ul.find_element_by_tag_name("ul")
            l += 1
        except:
            try:
                if levels != l:
                    toExplore = []
                    for li in ul.find_elements_by_tag_name("li"):
                        el = []
                        el.append(li.find_element_by_tag_name("a").text)
                        el.append(li.find_element_by_tag_name("a").get_attribute("href"))
                        toExplore.append(el)
                    for el in toExplore:
                        deparmentsHistory.append(el[0])
                        driver.get(el[1])
                        department[el[0]] = loop_and_open({}, marketPlace, limitResults, l)
                    print(department)
                    return department
                else:
                    scrape_department(deparmentsHistory[-1], marketPlace, limitResults)
                    return {}
            except:
                return {}
    return {}


def amazonBestSellers(mode, marketPlaces, limitResults=0):
    for marketPlace in marketPlaces:
        if open_url(marketPlace) == -1:
            return []
        # driver.get("https://www.amazon.com/Best-Sellers-Appliances/zgbs/appliances/ref=zg_bs_unv_la_1_3741261_1")
        departments = loop_and_open({}, marketPlace, limitResults)
        # print(departments)
    #     for department in departments.keys():
    #         loop_and_open(department, departments[department], marketPlace, limitResults)
        for x in bestSellers:
            x["limitResults"] = limitResults
            driver.get(x["htmlLinkPage"])
            x = scrape_detailed(x)
    if mode == 2:
        store_data()
    driver.quit()
    return bestSellers


mem = virtual_memory()
start = time.time()
op = amazonBestSellers(2, ["US"])
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
