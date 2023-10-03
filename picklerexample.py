from requests_html import AsyncHTMLSession
from urllib.parse import urlparse

import jsonpickle
import json


class VBook(object):
    def __init__(self, url):
        self.URL = url
    



    
    

class Booger(object):
    def __init__(self):
        self.list = [1,2,3,4,5]

class Blob(object):
    def __init__(self):
        self.boogers = []
    
    def addBooger(self, booger):
        self.boogers.append(booger)
        
blob = Blob()
booger = Booger()
blob.addBooger(booger)
blob.addBooger(booger)
blob.addBooger(booger)
blob.addBooger(booger)
blob.addBooger(booger)
blob.addBooger(booger)
pickleBlob = jsonpickle.encode(blob)
with open('shitface.txt','w') as f:
    json.dump(pickleBlob, f)
with open('shitface.txt', 'r') as g:
    repickleBlob = json.load(g)
blobTwin = jsonpickle.decode(repickleBlob)
print (f'blob: {vars(blob)}')
print (f'blobTwin: {vars(blobTwin)}')
