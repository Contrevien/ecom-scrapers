import pyspeedtest
from psutil import virtual_memory
import platform
import time
from pymongo import MongoClient

client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

def monitorAndLog(function, *parameters):
    start = time.time()
    result, errors = function(*parameters)
    print("Logging in database")
    end = time.time()
    log = {}
    s = pyspeedtest.SpeedTest()
    mem = virtual_memory()

    log["timestamp"] = int(time.time())
    log["scrapingTime"] = int((end-start)*100)/100
    if len(result) != 0:
        log["type"] = result[0]["type"]
    log["objectScraped"] = len(result)
    log["errors"] = errors
    # 1048576  # KB to GB

    log["OS"] = platform.linux_distribution()[0]
    log["OSVersion"] = platform.linux_distribution()[1]
    log["CPU"] = platform.processor()
    log["RAM"] = str((mem.total/1048576)/1000) + " GB"
    log["ping"] = str(int(s.ping()*100)/100)  + " ms"
    log["download"] = str(s.download()/1000000) + " Mbps"
    log["upload"] = str(s.upload()/1000000) + " Mbps"
    scraperDb.executionLog.insert_one(log)
    return result