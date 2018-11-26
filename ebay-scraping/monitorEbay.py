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
from scrapeEbay import scrapeEbay
import platform
from psutil import virtual_memory
from subprocess import check_output

timestamp = int(time.time())
errors = {}

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb


def monitorEbay(keyowrds, marketPlaces, sortBy, detailedResults=0, limitResults=0):
    updatedObjects = scrapeEbay(1, keyowrds, marketPlaces, sortBy, detailedResults, 1)
    collection = ""
    if detailedResults == 0:
        collection = "ebaySimpleProducts"
    else:
        collection = "ebayDetailedProducts"
    for x in updatedObjects:
            a = scraperDb[collection].find({"uniqueCode": x["uniqueCode"]})
            if a.count() == 0:
                print("Adding", x["uniqueCode"])
                scraperDb[collection].insert_one(x)
            else:
                for y in a:
                    for instance in y["searchParams"]:
                        if instance["keyword"] == x["searchParams"][0]["keyword"] and instance["limitResults"] == x["searchParams"][0]["limitResults"] and instance["sortBy"] == x["searchParams"][0]["sortBy"] and instance["marketPlace"] == x["searchParams"][0]["marketPlace"]:
                            print("Updating " + y["title"][:20])
                            instance["changingInfos"].extend(x["searchParams"][0]["changingInfos"])
                            break
                    else:
                        print("Adding new params " + y["title"][:20])
                        y["searchParams"].extend(x["searchParams"])

                    scraperDb[collection].find_one_and_replace({"_id": y["_id"]}, y)
    return updatedObjects

# mem = virtual_memory()
# start = time.time()
# op = monitorEbay(["sport watch"], ["US"], 1, 1, 2)
# print("Logging in database")
# end = time.time()
# log = {}

# log["timestamp"] = int(time.time())
# log["scrapingTime"] = int((end-start)*100)/100
# log["objectScraped"] = len(op)
# log["errors"] = errors
# log["type"] = "monitorEbay"
# # 1048576  # KB to GB

# log["RAM"] = str(mem.total/1048576*1024) + " GB"
# log["OS"] = platform.linux_distribution()[0]
# log["OSVersion"] = platform.linux_distribution()[1]
# log["CPU"] = {}
# for info in check_output(['lscpu']).decode('utf-8').split('\n'):
#     splitInfo = info.split(':')
#     if splitInfo[0] in ['Architecture', 'CPU op-mode(s)', 'Byte Order', 'CPU(s)', 'Thread(s) per core', 'Core(s) per socket', 'Socket(s)', 'Model name', 'CPU MHz']:
#         try:
#             log["CPU"][splitInfo[0]] = int(splitInfo[1].strip())
#         except:
#             log["CPU"][splitInfo[0]] = splitInfo[1].strip()
# log["ConnectionSpeed"] = {}
# speedCheck = check_output(['speedtest-cli', '--bytes']).decode('utf-8').split('\n')
# log["ConnectionSpeed"]["Upload"] = speedCheck[-2].split(':')[1].strip()
# log["ConnectionSpeed"]["Download"] = speedCheck[-4].split(':')[1].strip()
# log["ConnectionSpeed"]["Ping"] = speedCheck[-6].split(':')[1].strip()

# scraperDb.executionLog.insert_one(log)