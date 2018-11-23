from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import time
import json
from pymongo import MongoClient

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

def open_url(term, searchPeriod):
    term = term + " review"
    url = ""
    if searchPeriod == "x":
        url = "https://www.google.com/search?q=" + term
    else:
        url = "https://www.google.com/search?q=" + term + "&as_qdr=" + searchPeriod
    driver.get(url)

def get_links(number):
    results = []
    done = False
    while not done:
        links = ""
        try:
            links = driver.find_elements_by_class_name("r")
        except:
            errors["Search Results Class Error"] = 1
            return -1
        finalResults = []
        for r in links:
            if r.tag_name != "div" or r.text == "":
                continue
            finalResults.append(r)
        for r in finalResults:
            results.append(r.find_element_by_tag_name("a").get_attribute("href"))
            if len(results) >= number:
                flag = 1
                done = True
                break
        try:
            nextPage = driver.find_element_by_id("pnnext").get_attribute("href")
            driver.get(nextPage)
        except:
            done = True
    return results

def scroll_all():
    profile_scroll = 100
    prevTop = -1
    while True:
        driver.execute_script("window.scrollTo(0, " + str(profile_scroll) + ");")
        time.sleep(0.2)
        if prevTop == driver.execute_script("return window.pageYOffset;"):
            driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
            break
        prevTop = driver.execute_script("return window.pageYOffset;")
        profile_scroll += 500

    
def scrape_link(term, limit):
    splitTerm = term.split()
    try:
        scroll_all()
    except:
        print("Malicious Page")
        return []
    tags = []
    try:
        tags.extend(driver.find_elements_by_tag_name("p"))
    except:
        print("No p tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("span"))
    except:
        print("No span tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h1"))
    except:
        print("No h1 tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h2"))
    except:
        print("No h2 tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h3"))
    except:
        print("No h3 tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h4"))
    except:
        print("No h4 tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h5"))
    except:
        print("No h5 tags found")
    try:
        tags.extend(driver.find_elements_by_tag_name("h6"))
    except:
        print("No h6 tags found")

    results = []
    for tag in tags:
        try:
            for st in splitTerm:
                if st in tag.text.lower():
                    temp = {}
                    temp["text"] = tag.text
                    temp["tagType"] = tag.tag_name
                    results.append(temp)
                    break
        except Exception as e:
            errors[e] = 1
        if len(results) > limit and limit != 0:
            break
    return results
    

def scrapeGoogleSearch(term, searchPeriod, numberOfWebPages, limitResultsPerPage=0):
    
    dateFilter = {
        "Whatever date": "x",
        "Past hour": "h",
        "Past day": "d",
        "Past week": "w",
        "Past month": "m",
        "Past year": "y"
    }
    
    # search the term
    open_url(term, dateFilter[searchPeriod])

    # number of Results
    resultsNumber = ""
    try:
        resultsNumber = int("".join(driver.find_element_by_id("resultStats").text.split()[1].split(",")))
    except:
        resultsNumber = "NA"

    #get the links
    links = get_links(numberOfWebPages)
    print(len(links))
    results = []
    i = 1
    for link in links:
        if i > numberOfWebPages:
            break
        print("Opening page " + str(i))
        driver.get(link)
        thisSearch = scrape_link(term, limitResultsPerPage)
        temp = {}
        temp["timestamp"] = timestamp
        temp["keyword"] = term
        temp["searchEngine"] = "www.google.com"
        temp["numberOfWebPages"] = numberOfWebPages
        temp["limitResultsPerPage"] = limitResultsPerPage
        temp["searchResultsNumber"] = resultsNumber
        temp["pageLink"] = link
        temp["searchPeriod"] = searchPeriod
        temp["content"] = thisSearch
        results.append(temp)

        i += 1

    for x in results:
        scraperDb.googleSearch.insert_one(x)

scrapeGoogleSearch("apple watch", "Whatever date", 25)