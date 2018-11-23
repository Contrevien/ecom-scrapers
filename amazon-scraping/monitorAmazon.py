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
import platform


timestamp = int(time.time())
errors = {}

client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def monitorAmazon(keyowrds, marketPlaces, sortBy, detailedResults=0, limitResults=0):
    updatedObjects = scrapeAmazon(1, keyowrds, marketPlaces, sortBy, detailedResults, 1)
    for x in updatedObjects:
        if detailedResults == 0:
            a = scraperDb.amazonSimpleProducts.find({"asinCode": x["asinCode"], "sortBy": x["sortBy"], "type": x["type"], "marketPlace": x["marketPlace"], "keyword": x["keyword"]})
            if a.count() == 0:
                print("Adding", x["asinCode"])
                scraperDb.amazonSimpleProducts.insert_one(x)
            else:
                for y in a:
                    print("Updating", y["title"][:20])
                    y["changingInfos"].extend(x["changingInfos"])
                    scraperDb.amazonSimpleProducts.find_one_and_replace({"_id": y["_id"]}, y)

        elif detailedResults == 1:
            a = scraperDb.amazonDetailedProducts.find(
                {"asinCode": x["asinCode"], "sortBy": x["sortBy"], "type": x["type"], "marketPlace": x["marketPlace"], "keyword": x["keyword"]})
            if a.count() == 0:
                print("Adding", x["asinCode"])
                scraperDb.amazonDetailedProducts.insert_one(x)
            else:
                for y in a:
                    print("Updating", y["title"][:20])
                    y["changingInfos"].extend(x["changingInfos"])
                    scraperDb.amazonDetailedProducts.find_one_and_replace({"_id": y["_id"]}, y)
    return updatedObjects

start = time.time()
op = monitorAmazon(["sport watch"], ["US"], "Featured")
print("Logging in database")
end = time.time()
log = {}

log["timestamp"] = int(time.time())
log["scrapingTime"] = int((end-start)*100)/100
log["objectScraped"] = len(op)
log["errors"] = errors
log["type"] = "monitorAmazon"
# 1048576  # KB to GB

log["OS"] = platform.linux_distribution()[0]
log["OSVersion"] = platform.linux_distribution()[1]
log["CPU"] = platform.processor()
scraperDb.executionLog.insert_one(log)