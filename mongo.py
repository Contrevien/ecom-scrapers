from pymongo import MongoClient
import json
from bson.objectid import ObjectId

# json_file = open('result.json')
# json_str = json_file.read()
# json_data = json.loads(json_str)
client = MongoClient(
    'mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
db = client.test_amazon
col = db['amazon']
count = 0
for x in db.col.find({"_id": ObjectId("5be8330316209a0f1cb204c5")}):
    print(x)
    count += 1
    if count == 16:
        break

# client = MongoClient(port=27017)
# mydb = client.amazon
# mycol = mydb['scrapeAmazon']

# for x in mydb.mycol.find({"marketPlace": "US"}):
#     print(x)
