from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import urllib.request
import time
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from scrapeAmazon import scrapeAmazon


timestamp = int(time.time())
errors = {}

client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def monitorAmazon(keyowrds, marketPlaces, sortBy=0, detailedResults=0, limitResults=0):
    updatedObjects = scrapeAmazon(
        keyowrds, marketPlaces, sortBy, detailedResults, 1, 2)
    for x in updatedObjects:
        if detailedResults == 0:
            a = scraperDb.amazonSimpleProducts.find(
                {"asinCode": x["asinCode"], "sortBy": x["sortBy"], "type": x["type"], "marketPlace": x["marketPlace"], "keyword": x["keyword"]})
            if a.count() == 0:
                print("Adding", x["asinCode"])
                scraperDb.amazonSimpleProducts.insert_one(x)
            else:
                for y in a:
                    print("Updating", y["title"][:20])
                    if y["resultsNumber"][-1]["resultsCount"] != x["resultsNumber"][-1]["resultsCount"]:
                        y["resultsNumber"].extend(x["resultsNumber"])
                    else:
                        y["resultsNumber"][-1]["timestamp"] = x["resultsNumber"][-1]["timestamp"]
                    if y["customersReviewsCounts"][-1]["customersReviewsCount"] != x["customersReviewsCounts"][-1]["customersReviewsCount"]:
                        y["customersReviewsCounts"].extend(
                            x["customersReviewsCounts"])
                    else:
                        y["customersReviewsCounts"][-1]["timestamp"] = x["customersReviewsCounts"][-1]["timestamp"]
                    if y["ratingsOf5Stars"][-1]["ratingOf5Stars"] != x["ratingsOf5Stars"][-1]["ratingOf5Stars"]:
                        y["ratingsOf5Stars"].extend(x["ratingsOf5Stars"])
                    else:
                        y["ratingsOf5Stars"][-1]["timestamp"] = x["ratingsOf5Stars"][-1]["timestamp"]
                    if y["prices"][-1]["price"] != x["prices"][-1]["price"]:
                        y["prices"].extend(x["prices"])
                    else:
                        y["prices"][-1]["timestamp"] = x["prices"][-1]["timestamp"]
                    scraperDb.amazonSimpleProducts.find_one_and_replace(
                        {"_id": y["_id"]}, y)

        elif detailedResults == 1:
            a = scraperDb.amazonDetailedProducts.find(
                {"asinCode": x["asinCode"], "sortBy": x["sortBy"], "type": x["type"], "marketPlace": x["marketPlace"], "keyword": x["keyword"]})
            if a.count() == 0:
                print("Adding", x["asinCode"])
                scraperDb.amazonDetailedProducts.insert_one(x)
            else:
                for y in a:
                    print("Updating", y["title"][:20])
                    if y["resultsNumber"][-1]["resultsCount"] != x["resultsNumber"][-1]["resultsCount"]:
                        y["resultsNumber"].extend(x["resultsNumber"])
                    else:
                        y["resultsNumber"][-1]["timestamp"] = x["resultsNumber"][-1]["timestamp"]
                    if y["customersReviewsCounts"][-1]["customersReviewsCount"] != x["customersReviewsCounts"][-1]["customersReviewsCount"]:
                        y["customersReviewsCounts"].extend(
                            x["customersReviewsCounts"])
                    else:
                        y["customersReviewsCounts"][-1]["timestamp"] = x["customersReviewsCounts"][-1]["timestamp"]
                    if y["ratings"][-1]["rating"] != x["ratings"][-1]["rating"]:
                        y["ratings"].extend(x["ratings"])
                    else:
                        y["ratings"][-1]["timestamp"] = x["ratings"][-1]["timestamp"]

                    if y["prices"][-1]["price"] != x["prices"][-1]["price"]:
                        y["prices"].extend(x["prices"])
                    else:
                        y["prices"][-1]["timestamp"] = x["prices"][-1]["timestamp"]
                    scraperDb.amazonDetailedProducts.find_one_and_replace(
                        {"_id": y["_id"]}, y)


monitorAmazon(["sport watch"], ["US"])
