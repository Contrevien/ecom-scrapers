from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import csv
import urllib.request
from collections import Counter
import time
import json

class Webpage(object):

    def __init__(self, url):
        ch = os.getcwd() + '/tools/chromedriver'
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("log-level=3")
        self.driver = webdriver.Chrome(options=options, executable_path=ch)
        self.wait = WebDriverWait(self.driver, 600)

    def scrapeAmazon(self, keywords, marketPlace, sortBy, detailedResults, limitResults=-1):
        errors = []
        regionSearch = []
        for region in marketPlace:
            if region == "US":
                url = "https://www.amazon.com/"
            else:
                url = "https://www.amazon."+region.lower()+"/"
            matchWord = []
            if region == "US" or region == "IN":
                matchWord.append("Customers who bought this item also bought")
                matchWord.append("Customers also shopped for")
            if region == "FR":
                matchWord.append("Les clients ayant acheté cet article ont également acheté")
                
            keywordSearch = dict()
            for keyword in keywords:
                keywordSearch[keyword] = []
                #type in the search bar
                print("Loading..")
                self.driver.get(url)
                try:
                    self.driver.find_element_by_id("twotabsearchtextbox").send_keys(keyword+"\n")
                except:
                    errors.append("Possible error in search box")
                    break
                print("Searching..", keyword)
                #save timestamp
                timestamp = int(time.time())
                #get the number of results
                try:
                    result_count = self.driver.find_element_by_id("s-result-count").text
                    result_count = result_count.split()
                    result_count = result_count[3]
                    #get results list
                except:
                    errors.append("Possible error in result count")

                done = False
                start = 0
                search = []
                end = 50000000
                if not (limitResults == -1):
                    end = limitResults
                while len(search) < end:
                    temp = dict()
                    temp["timestamp"] = timestamp
                    temp["resultsNumber"] = result_count
                    temp["keyword"] = keyword
                    temp["marketplace"] = region;
                    if limitResults==-1:
                        temp["limitResults"] = "No limit"
                    else:
                        temp["limitResults"] = limitResults
                    if detailedResults == 1:
                        temp["type"] = "scrapeAmazonDetailed"
                    else:
                        temp["type"] = "scrapeAmazonSimple"
                    ul = self.driver.find_element_by_id("s-results-list-atf")

                    #go to element or next page
                    el = ul.find_element_by_id("result_" + str(start))
                    self.driver.get(el.find_element_by_class_name("a-link-normal").get_attribute("href"))
                
                    print("Scraping", start)
                    #title
                    try:
                        title = self.driver.find_element_by_id("productTitle").text
                        title = title.strip()
                        temp["title"] = title
                    except:
                        temp["title"] = "NA"
                        errors.append("Possible Error in Title")

                    #price
                    try:
                        fetched_price = self.driver.find_element_by_id("priceblock_ourprice").text
                        temp["price"] = fetched_price
                    except:
                        try:
                            fetched_price = self.driver.find_element_by_id("priceblock_saleprice").text    
                            temp["price"] = fetched_price
                        except:
                            temp["price"] = "NA"
                            errors.append("Price not found")

                    #descriptions, only if detailed
                    if detailedResults == 1:
                        try:
                            des_div = self.driver.find_element_by_id("feature-bullets")
                            des_spans = des_div.find_elements_by_class_name("a-list-item")
                            description = []
                            for des in des_spans:
                                description.append(des.text)
                            description = "".join(description)
                            temp["description"] = description
                        except:
                            temp["description"] = "NA"
                            errors.append("Description not found")

                    #reviews
                    try:
                        review_a = self.driver.find_element_by_id("reviewsMedley")
                        review_b = review_a.find_element_by_id("dp-summary-see-all-reviews")
                        reviews = int(review_b.find_element_by_tag_name("h2").text.split()[0])
                        temp["customersReviewsCount"] = reviews
                        if detailedResults == 1:
                            table = review_a.find_element_by_id("histogramTable")
                            percents = table.find_elements_by_class_name("a-text-right")
                            review_arr = []
                            for i in percents:
                                per = int(i.text[:-1])
                                review_arr.append(int(reviews*(per/100)))
                            ratings = dict()
                            for i in range(5):
                                ratings[str(5-i)+"stars"] = review_arr[i]
                            temp["rating"] = ratings
                    except:
                        temp["rating"] = "NA"
                        errors.append("Review not found")

                    #specs
                    if detailedResults == 1:
                        productSpecs = dict()
                        try:
                            self.driver.find_element_by_id("softlinesTechnicalSpecificationsLink").click()
                            
                            tbody = self.driver.find_element_by_id("technicalSpecifications_section_1")
                            heads = tbody.find_elements_by_tag_name("th")
                            values = tbody.find_elements_by_tag_name("td")
                            
                            for i in range(len(heads)):
                                productSpecs[heads[i].text.strip()] = values[i].text.strip()
                            self.driver.back()
                        except:
                            temp["productSpecs"] = "NA"

                    #similar
                    if detailedResults == 1:
                        try:
                            more = []
                            carousels = []
                            sim_i = 1
                            while True:
                                try:
                                    carousels.append(self.driver.find_element_by_id("sims-consolidated-"+ str(sim_i) +"_feature_div"))
                                    sim_i += 1
                                except:
                                    break
                            selected = None
                            for c in carousels:
                                try:
                                    testWord =  c.find_element_by_class_name("a-carousel-heading").text
                                    flag = 0
                                    for word in matchWord:
                                        if word in testWord:
                                            print("Yes")
                                            selected = c
                                            break
                                    if flag == 1:
                                        break
                                except:
                                    continue
                            print(selected)
                            ol = selected.find_element_by_tag_name("ol")
                            more.extend(ol.find_elements_by_tag_name("li"))
                            customersAlsoBought = []
                            for i in more:
                                temp2 = {}
                                print(i)
                                temp2["htmlLink"] = i.find_element_by_tag_name("a").get_attribute("href")
                                print(temp2["htmlLink"])
                                temp2["ratingOf5Stars"] = i.find_elements_by_tag_name("a")[1].get_attribute("title").split()[0]
                                print(temp2["ratingOf5Stars"])
                                details = i.text.split('\n')
                                try:
                                    temp2["title"] = details[0]
                                except:
                                    temp2["title"] = "NA"
                                try:
                                    temp2["customersReviewsCount"] = details[1]
                                except:
                                    temp2["customersReviewsCount"] = "NA"
                                try:
                                    temp2["price"] = details[2]
                                except:
                                    temp2["price"] = "NA"
                                customersAlsoBought.append(temp2)
                            temp["customersAlsoBought"] = customersAlsoBought
                        except:
                            temp["customersAlsoBought"] = "NA"
                            errors.append("Customers also bought error")
                    temp["htmlPageLink"] = self.driver.current_url
                    search.append(temp)
                    self.driver.back()
                    start += 1
                keywordSearch[keyword] = search
            regionSearch.append(keywordSearch)
        print(errors)
        self.driver.quit()
        return regionSearch

obj = Webpage('https://www.amazon.com/');

#parameters of scrapeAmazon([keywords], [marketplaces], sortBy, detailed, limit)
ans = obj.scrapeAmazon(["sport watch", "rolex"], ["US", "FR"], 1, 1, 2)
js = json.dumps(ans)
with open('result.json','w') as fp:
    fp.write(js)
    
# TODO
# - Complete customersAlsoBought
# - Add loop for different marketplaces
