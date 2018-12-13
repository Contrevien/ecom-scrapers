from pytrends.request import TrendReq
from pymongo import MongoClient
import time
import os
import datetime as dt
import pandas as pd
from dateutil.relativedelta import relativedelta
from psutil import virtual_memory
import platform
from subprocess import check_output

timestamp = int(time.time())
client = MongoClient("mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb")
scraperDb = client.scraperDb

def get_trends(mode, keywords, geo=None, startDate=dt.datetime.now(), endDate=dt.datetime.now() - relativedelta(years=5)):
    pytrends = TrendReq(hl="en-US", tz=360)

    finalObject = []

    for keyword in keywords:
        temp = {}
        temp["timestamp"] = timestamp
        temp["keyword"] = keyword
        temp["startDate"] = startDate.strftime("%Y-%m-%d")
        temp["endDate"] = endDate.strftime("%Y-%m-%d")
        kw = [keyword]
        pytrends.build_payload(kw, cat=0, timeframe="today 5-y", geo="", gprop="")
        trend = pytrends.interest_over_time()

        region = pytrends.interest_by_region()
        regionTrends = region.to_dict()
        regionTrends = regionTrends[keyword]
        related_topics = pytrends.related_topics()
        related_queries = pytrends.related_queries()

        timeMap = pd.date_range(start=endDate.strftime("%m/%d/%Y"), periods=261, freq="7D")
        
        temp["trend"] = {}
        for i in range(len(trend)):
            temp["trend"][str(timeMap[i]).split()[0]] = int(trend.iloc[i][0])

        temp["trendByRegion"] = {}
        for x in regionTrends.keys():
            name = ""
            for ch in x:
                if ch.isalpha() or ch==" ":
                    name += ch
            temp["trendByRegion"][name] = regionTrends[x]

        temp["relatedTopics"] = []
        for x in related_topics[keyword].to_dict()["title"].values():
            name = ""
            for ch in x:
                if ch.isalpha() or ch==" ":
                    name += ch
            temp["relatedTopics"].append(name.strip())
        
        temp["topRelatedQueries"] = {}
        rqdf = related_queries[keyword]["top"]
        for i in range(len(rqdf)):
            name = ""
            for ch in rqdf.iloc[i][0]:
                if ch.isalpha() or ch==" ":
                    name += ch
            temp["topRelatedQueries"][name] = int(rqdf.iloc[i][1])
        
        temp["risingRelatedQueries"] = {}
        rqdf = related_queries[keyword]["rising"]
        for i in range(len(rqdf)):
            name = ""
            for ch in rqdf.iloc[i][0]:
                if ch.isalpha() or ch==" ":
                    name += ch
            temp["risingRelatedQueries"][name] = int(rqdf.iloc[i][1])

        finalObject.append(temp)
    
    if mode == 2:
        for x in finalObject:
            scraperDb.googleTrends.insert_one(x)
    return finalObject

mem = virtual_memory()
start = time.time()
op = get_trends(2, ["apple watch", "mi band"])
end = time.time()
# log = {}

# log["timestamp"] = int(time.time())
# log["scrapingTime"] = int((end-start)*100)/100
# log["objectScraped"] = len(op)
# log["errors"] = errors
# log["type"] = "scrapeEbay"
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