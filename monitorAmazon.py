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
        keyowrds, marketPlaces, sortBy, detailedResults, limitResults, 2)
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
                    y["resultsNumber"].extend(x["resultsNumber"])
                    y["customersReviewsCounts"].extend(
                        x["customersReviewsCounts"])
                    y["ratingsOf5Stars"].extend(x["ratingsOf5Stars"])
                    y["prices"].extend(x["prices"])
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
                    y["resultsNumber"].extend(x["resultsNumber"])
                    y["customersReviewsCounts"].extend(
                        x["customersReviewsCounts"])
                    y["ratings"].extend(x["ratings"])
                    y["prices"].extend(x["prices"])
                    scraperDb.amazonDetailedProducts.find_one_and_replace(
                        {"_id": y["_id"]}, y)
