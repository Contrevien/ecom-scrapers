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
from amazonBestSellers import amazonBestSellers
import platform


timestamp = int(time.time())
errors = {}

test = {
    "Computers & Accessories": {
        "Desktops": dict(),
    },
    "Amazon Devices & Accessories": {
        "Amazon Devices": {
            "Home Security from Amazon": dict(),
        },
    },
}

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def monitorBestSellers(departments, marketPlaces):
    updatedOnes = amazonBestSellers(1, departments, marketPlaces, 0)
    for x in updatedOnes:
        a = scraperDb.bestSellers.find(
            {"title": x["title"], "type": x["type"], "marketPlace": x["marketPlace"], "department": x["department"], "subDepartment": x["subDepartment"], "subSubDepartment": x["subSubDepartment"]})
        if a.count() == 0:
            print("Adding", x["title"][:20])
            scraperDb.bestSellers.insert_one(x)
        else:
            for y in a:
                print("Updating", y["title"][:20])
                y["changingInfos"].extend(x["changingInfos"])
                scraperDb.bestSellers.find_one_and_replace({"_id": y["_id"]}, y)
    return updatedOnes

start = time.time()
op = monitorBestSellers(test, ["US"])
print("Logging in database")
end = time.time()
log = {}

log["timestamp"] = int(time.time())
log["scrapingTime"] = int((end-start)*100)/100
log["objectScraped"] = len(op)
log["errors"] = errors
log["type"] = "monitorBestSellers"
# 1048576  # KB to GB

log["OS"] = platform.linux_distribution()[0]
log["OSVersion"] = platform.linux_distribution()[1]
log["CPU"] = platform.processor()
scraperDb.executionLog.insert_one(log)