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

client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def monitorBestSellers(departments, marketPlaces):
    updatedOnes = amazonBestSellers(departments, marketPlaces, 0, 2)
    for x in updatedOnes:
        a = scraperDb.bestSellers.find(
            {"title": x["title"], "type": x["type"], "marketPlace": x["marketPlace"], "department": x["department"], "subDepartment": x["subDepartment"], "subSubDepartment": x["subSubDepartment"]})
        if a.count() == 0:
            print("Adding", x["title"][:20])
            scraperDb.bestSellers.insert_one(x)
        else:
            for y in a:
                print("Updating", y["title"][:20])
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
                scraperDb.bestSellers.find_one_and_replace(
                    {"_id": y["_id"]}, y)
