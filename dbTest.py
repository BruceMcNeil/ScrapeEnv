import pymongo
myClient = pymongo.MongoClient('mongodb://localhost:27017')
myDB = myClient["VBooks"]
dbList = myClient.list_database_names()
if ("VBooks" in dbList):
    print (f'Found VBooks database')
else:
    print(f'VBooks database not found')

imagesCollection = myDB['images']
contentCollection = myDB['content']
textCollection = myDB['text']
