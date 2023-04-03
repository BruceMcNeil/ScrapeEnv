import requests
from requests_html import HTMLSession
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import html
import re
import jsonpickle
import json
import time
import vbookDb
import textract
import tiktoken


class VBook(object):
    def __init__(self, 
                 url:str = 'https://gutenberg.org/cache/epub/29494/pg29494-images.html',
                 start_phrase:str = '*** START OF THE PROJECT GUTENBERG EBOOK',
                 end_phrase:str = 'END OF THE PROJECT GUTENBERG',
                 debug:bool = False):
        self.debug = debug
        self.URL = url
        self.bookURL = url
        self.end_tag = end_phrase
        self.start_tag = start_phrase
        self.debug = debug
        self.errorMessage = ''
        self.bookTitle = "book-not-found"
        self.bookAuthor = "author-not-found"
        self.bookSubject = "subject-not-found"
        self.bookOgTitle = "og.title-not-found"
        self.bookOgSubject = "og.subject-not-found"
        self.bookImage = "book image not found"
        self.pageRe = re.compile("page[ivxld0-9].*")
        self.numberRe = re.compile("\[([ivxld0-9].*)\]") 
        self.pageNumbers = None
    
    def processHtmlSource(self) -> bool:
        result = False
        try:
            self.phase = '[parse url]'
            self.step = '[get rootURL]'            
            self.rootURL = self.parseURL(self.URL)
            self.phase = '[get content]'
            self.step = '[download content]'                
            self.bookHTML = self.getContent()
            self.step = '[parse content]'
            self.soup = BeautifulSoup(self.bookHTML, 'html5lib')
            self.step = '[parse book metadata]'
            self.processMetaData()
            self.step = '[parse book page numbers]'
            self.pageNumbers = self.getPageNumbers()
            self.step = '[collect image refs]'
            self.getImageRefs()
            self.step = '[get textual region of interest]'
            self.getSignificantText()
            self.step = '[build timeline]'
            self.buildTimeline()
            self.step = '[output products]'
            self.outputProducts()
            result = True
        except:
            raise Exception(
                f'VBook initialization failed in phase {self.phase} step {self.step} {self.errorMessage}'
                )
        return (result)

    def getContent(self) -> str:
        asession = HTMLSession()
        r = asession.get(self.URL)
        return r.content

    def parseURL(self, url) -> str:
        urlParts = urlparse(url)
        if (self.debug):
            print (repr(urlParts))
            print (f"Path is  {urlParts.path}")
        components = urlParts.path.split('/')
        rootPart = "/"
        if (self.debug):
            print (f"Elements: {components}")
        components.pop() # remove last element111
        if (self.debug):
            print (f"Elements: {components}")
        components.pop(0) # remove the inexplicable blank element at start of list
        if (self.debug):
            print (f"Elements: {components}")
        for element in components:
            rootPart = rootPart + element + '/'
        rootURL = f'{urlParts.scheme}://{urlParts.netloc}{rootPart}'
        if (self.debug):
            print (f"rootURL: {rootURL}")
        return rootURL
    
    def metaPrint(self, obj, attrib, name, isURL:bool = False) -> str:
        nugget = obj[attrib]
        if (self.debug):
            print(f"---> '{name}' is: '{nugget}")
        unes = html.unescape(nugget)
        unes = unes.replace('\n', ' -- ')
        if (isURL == False):
            unes = unes.replace('\\',' ')
            unes = unes.replace('/',' ')
            unes = unes.replace(':',' -- ')
            unes = unes.replace('?',' ')
        unes = unes.replace('*',' ')        
        unes = unes.replace('"',' ')
        unes = unes.replace("'",'')
        unes = unes.replace('<',' ')
        unes = unes.replace('>',' ')    
        unes = unes.replace('|',' ')
        if (self.debug):
            print(f"unescaped: {unes}")
            print(f"---> at sourceline({obj.sourceline}) pos({obj.sourcepos})\n")
        return unes

    def processMetaData(self):
        metas = self.soup.find_all('meta')
        for meta in metas:
            try:
                meta_name = meta['name']
                if (meta_name == 'dc.subject'):
                    self.bookSubject = self.metaPrint(meta, 'content', 'Subject')
                elif (meta_name == 'dc.creator'):
                    self.bookAuthor = self.metaPrint(meta, 'content', 'Creator')
                elif (meta_name == 'dc.title'):
                    self.bookTitle = self.metaPrint(meta, 'content', 'Title')
                elif (meta_name == 'og.title'):
                    self.bookOgTitle = self.metaPrint(meta, 'content', 'OgTitle')            
                elif (meta_name == 'og.subject'):
                    self.bookOgSubject = self.metaPrint(meta, 'content', 'Subject') 
            except:
                if (self.debug):
                    print(f"processMetaData. No name for meta tag: {meta}")
            try:
                meta_property = meta['property']
                if (meta_property == 'og:url'):
                    self.bookURL = self.metaPrint(meta, 'content', 'URL', True)            
                if (meta_property == 'og:image'):
                    self.bookImage = self.metaPrint(meta, 'content', 'Image', True)            
            except:
                pass

    def getPageNumbers(self) -> object:
        anchors = None
        try:
            anchors = self.soup.find_all('a', id = self.pageRe)
            for anchor in anchors:
                pageMatch = self.numberRe.match(anchor.string)
                page_num = pageMatch.group(1)
                if (self.debug):
                    print(f"{repr(anchor)} -> {page_num} on sourceline {anchor.sourceline} position {anchor.sourcepos}")
        except:
            pass
        return anchors

    def qualify_href(self, tag) -> bool:
        result = False
        c1 = False
        c2 = False
        if (tag.has_attr('href') and not tag.has_attr('class')):
            try:
                z = tag['href'].index(".png")
                c1 = True
            except:
                pass
                # idiot to throw exception from index functions duhhh
            try:
                z = tag['href'].index(".jpg")
                c2 = True
            except:
                pass
        result = c1 or c2
        return result
    
    def qualify_caption(self, tag) -> bool:
        c1 = False
        try:
            if (tag.has_attr('class')):
                if (tag['class'] == 'caption'):
                    c1 = True
        except:
            pass            
        return c1
    
    def getImageRefs(self):
        try:
            self.images_href = self.soup.find_all(self.qualify_href)
            self.images_src = self.soup.find_all('img')
            self.allImages = AllImages(self.images_src, self.rootURL, self.URL)
            self.figcenters = self.soup.find_all(class_ = 'figcenter')
            self.figrights = self.soup.find_all(class_ = "figright")
        except:
            raise('failed in getImageRefs')
        

    def getSignificantText(self) -> bool:
        result = False
        self.texts = self.soup.get_text()
        start_index = 0
        end_index = -1
        try:
            end_index = self.texts.index(self.end_tag)
            self.texts = self.texts[:end_index]
            start_index = self.texts.index(self.start_tag)
            start_index = start_index + len(self.start_tag)
            self.texts = self.texts[start_index:]     
            result = True       
        except:
            raise ('Failed in getSignificantText')
        return result
    
    def getHTML(self) -> str:
        return self.bookHTML

    def traverse(self, rootTags, newIndent):
        if (self.debug):
            print (f'Traverse at {repr(self.timeline)}')
        try:
            for element in rootTags:
                element_type = repr(type(element))
                if (element_type != "<class 'bs4.element.Tag'>"):
                    # these are bs4.element.NavigableString
                    # print (f'Level {newIndent}> {repr(self.timeline)} [{type(element)}] : {element.string}')
                    self.timeline.checkStartSequence(element.string)
                else:
                    if (self.timeline.setTimeLine(element.sourceline, element.sourcepos) == True):
                        if (len(element.contents) != 0):
                            self.traverse(element.contents, newIndent + 1)   
                    else:
                        if (self.debug):
                            print ('TERMINATING DUE TO END OF TIMELINE')
                        break
        except Exception as exception:
            print(f'In traverse(): {exception.args} {exception} {vars(exception)}')


    def scanToCollector(self, rootTags):
        for element in rootTags:
            element_type = repr(type(element))
            if (element_type != "<class 'bs4.element.Tag'>"):
                # these are bs4.element.NavigableString --> render to collector (global instance of TTSCollector class
                if (self.timeline.positionIsInContentWindow(self.collectTimeLine.timeline_line, self.collectTimeLine.timeline_pos)):
                    # print (f'Level {newIndent}> {repr(timeline)} [{type(element)}] : {element.string}')
                    self.textCollector.addContent(self.collectTimeLine.timeline_line, self.collectTimeLine.timeline_pos, element.string)
            else:
                # these are Tags
                if (self.collectTimeLine.setTimeLine(element.sourceline, element.sourcepos) == True):
                    if (len(element.contents) != 0):
                        self.scanToCollector(element.contents)   
                else:
                    # reached the end of content
                    break

    def buildTimeline(self) -> bool:
        result = False
        try:
            self.tags = self.soup.find_all(True)
            self.timeline = Timeline() 
            self.traverse(self.tags, 0)
            self.textCollector = TTSCollector()
            self.collectTimeLine = Timeline()
            self.scanToCollector(self.tags)
            self.content = self.textCollector.getContent()              
            result = True
        except Exception as e:
            print(f'Exception in buildTimeLine: {e} {e.args} {vars(e)}')
            raise Exception("VBook unable to build timeline")
        return result
    
    def outputProducts(self) -> bool:
        result = True
        if (self.debug):
            for ttsContent in self.content:
                print(f'[{ttsContent.line}:{ttsContent.pos}] {ttsContent.text}')
        textFileName = f'INCOMING/{self.bookTitle}.{self.bookAuthor}.txt'
        rc = self.textCollector.dumpContentToFile(textFileName)
        result &= rc
        # rc = self.textCollector.dumpTextToDB(self.dbClient, 'text')
        contentFileName = f'CONTENT/{self.bookTitle}.{self.bookAuthor}.json.content.txt'
        rc = self.textCollector.dumpContentJsonToFile(contentFileName)
        result &= rc
        #rc = self.textCollector.dumpContentToDB(self.dbClient, 'content')
        result &= rc
        imagesFileName = f'CONTENT/{self.bookTitle}.{self.bookAuthor}.json.images.txt'
        rc = self.allImages.dumpImagesJsonToFile(imagesFileName)
        result &= rc
        #rc = self.allImages.dumpImagesToDB(self.dbClient, 'images')
        htmlFileName = f'INCOMING/{self.bookTitle}.{self.bookAuthor}.html'
        rc = self.textCollector.dumpToFile(htmlFileName, self.bookHTML)
        self.htmlFileName = htmlFileName
        result &= rc
        return (result)
    
    def getText(self) -> str:
        return self.textCollector.extractTextFromHTML(self.htmlFileName)
    
    def endOfVBook(self):
        pass
    #
    # END OF CLASS Vbook
    #

class ImageContent(object):
    def __init__(self, image):
        self.line = image.sourceline
        self.pos = image.sourcepos
        self.text = image['src']

class AllImages(object):
    def __init__(self, images, rootURL, URL):
        self.rootURL = rootURL
        self.URL = URL
        self.images = []
        for image in images:
            imageContent = ImageContent(image)
            self.images.append(imageContent)

    def dumpImagesJsonToFile(self, fileName) -> bool:
        rc = False
        try:
            jsonObject = jsonpickle.encode(self)
            with open(fileName, 'w', encoding='utf-8') as f:
                f.write(jsonObject)
            rc = True
        except:
            pass
        return rc
    
    def dumpImagesToDB(self, client, collectionName) -> bool:
        return True

class Timeline(object):
    def __init__(self, startSequence = "*** START OF THE PROJECT GUTENBERG", endSequence = "*** END OF THE PROJECT GUTENBERG", debug:bool = False):
        self.timeline_line = 0
        self.timeline_pos = 0
        self.contentStartTime = "[-1:-1]"
        self.contentEndTime = "[-1:-1]"
        self.contentStartLine = -1
        self.contentStartPos = -1
        self.contentEndLine = -1
        self.contentEndPos = -1
        self.startSequence = startSequence
        self.endSequence = endSequence
        self.debug = debug  

    def setTimeLine(self, new_line, new_pos):
        noViolation = True
        if (new_line < self.timeline_line):
            if (self.debug):
                print (f'LINE TIMELINE VIOLATION!!! new [{new_line}:{new_pos}] old [{self.timeline_line}:{self.timeline_pos}]')
            noViolation = False
        if (new_line == self.timeline_line and new_pos < self.timeline_pos):
            if (self.debug):
                print (f'POS TIMELINE VIOLATION!!! new [{new_line}:{new_pos}] old [{self.timeline_line}:{self.timeline_pos}]')
            noViolation = False  
        if (noViolation == True):        
            self.timeline_line = new_line
            self.timeline_pos = new_pos
        return noViolation

    def printTimeLine(self):
        print (f'[{self.timeline_line}:{self.timeline_pos}]')

    def __str__(self):
        return f'line: {self.timeline_line} pos: {self.timeline_pos}'
    
    def __repr__(self):
        return f'[{self.timeline_line}:{self.timeline_pos}]'
    
    def checkStartSequence(self, candidate):
        if (self.startSequence in candidate):
            # self.contentStartTime = repr(self)
            self.contentStartLine = self.timeline_line
            self.contentStartPos = self.timeline_pos
        if (self.endSequence in candidate):
            # self.contentEndTime = repr(self)
            self.contentEndLine = self.timeline_line
            self.contentEndPos = self.timeline_pos

    def positionIsInContentWindow(self, line, pos):
        criterion = False
        if (line > self.contentStartLine and line < self.contentEndLine):
            criterion = True
        return criterion

class TTSContent(object):
    def __init__(self, line, pos, text):
        unes = html.unescape(text)
        """
        unes = unes.replace('\n', ' -- ')
        unes = unes.replace('\\',' ')
        unes = unes.replace('/',' ')
        unes = unes.replace(':',' -- ')
        unes = unes.replace('*',' ')
        unes = unes.replace('?',' ')
        """
        unes = unes.replace('"',' ')
        unes = unes.replace("'",'')
        """
        unes = unes.replace('<',' ')
        unes = unes.replace('>',' ')
        unes = unes.replace('|',' ')
        """
        self.line = line
        self.pos = pos
        self.text = unes

        self.vbookText = vbookDb.VBookText()       
        self.vbookText.line = line
        self.vbookText.pos = pos
        self.vbookText.text = unes

        
    def __str__(self):
        print(f'[{self.line}:{self.pos}] {self.text}')

    def __repr__(self):
        print(f'[{self.line}:{self.pos}] {self.text}')       


class TTSCollector(object):
    def __init__(self):
        self.content = []
 
    def __str__(self):
        print(f'TTSCollector: {len(list(self.content))} content lines')
    
    def __repr__(self):
        print(f'TTSCollector: {len(list(self.content))} content lines')

    def getContent(self):
        return self.content
    
    def addContent(self, line, pos, text):
        tc = TTSContent(line, pos, text)
        self.content.append(tc)

    def dumpContentToFile(self, fname) -> bool:
        rc = False
        try:
            with open(fname, 'w', encoding="utf-8") as f:
                for tc in self.content:
                    f.write(tc.text)
                    # print(tc.line)
            rc = True
        except:
            print('Error in TTSCollector.dumpContentToFile')
        return rc
    
    def dumpToFile(self, fname, content:str) -> bool:
        rc = False
        try:
            with open(fname, 'w', encoding="utf-8") as f:
                f.write(str(content, 'UTF-8'))
            rc = True
        except Exception as e:
            print(f'Error in TTSCollector.dumpDumpToFile. {e.args}\n{e.__traceback__}\n {e.__annotations__}')
        return rc 

    def extractTextFromHTML(self, fname) -> str:
        result = ""
        try:
            with open(fname, 'r') as f:
                rawHTML = f.read()
                soup = BeautifulSoup(rawHTML, "html.parser")
                decodedString = soup.prettify(formatter=None)
                result = decodedString
        except Exception as e:
            print(f'Error in extractTextFromHTML {e.__annotations__}')
        return result  
    
    def dumpTextToDB(self, client, collectionName):
        pass
        
    def dumpContentJsonToFile(self, fname) -> bool:
        rc = False
        try:
            with open(fname, 'w', encoding="utf-8") as f:
                jsonContent = jsonpickle.encode(self)
                # to reconstitute TTSCollector:
                #   use jsonContent = json.load(f)
                #   newTTSCollector = jsonpickle.decode(jsonContent)
                json.dump(jsonContent, f)
            rc = True
        except:
            print('Error in TTSCollector.dumpContentToFile')
        return rc 

    def dumpContentToDB(self, client, collectionName) -> bool:
        return True

"""
    sample usage of class VBook
"""
if __name__ == "__main__":
    # todo use args to pass the input file name or single URL, also TEXT only flag or auto check th

  

    with open('HTMLBookURLsToScan.txt', 'r') as f:
        htmlBookPaths = f.readlines()
        totalStart = time.perf_counter()
        bookCounter = 0
        for htmlBook in htmlBookPaths:
            startTime = time.perf_counter()            
            htmlBookPath = htmlBook.replace('\n','')
            print(f'TODO: remove DB entries for this book')
            vbook = None
            if (len(htmlBookPath) > 0):
                bookCounter = bookCounter + 1
                vbook = VBook(htmlBookPath)
                vbook.processHtmlSource()
                plainText = vbook.getText()
                print(f'textTract htmlText: {plainText}')
            endTime = time.perf_counter()
            ms = endTime - startTime
            print(f"Processed in {ms:.02f} s : {htmlBookPath}")
        totalEnd = time.perf_counter()
        dt = totalEnd - totalStart
        print(f"In {dt:.02f} s collected {bookCounter} vbooks")        

    #  htmlBookPath = 'https://gutenberg.org/cache/epub/29494/pg29494-images.html'
    # 'https://gutenberg.org/cache/epub/67699/pg67699-images.html'
    # 'https://gutenberg.org/cache/epub/54653/pg54653-images.html'
    # 'https://gutenberg.org/cache/epub/29494/pg29494-images.html'
    #  vbook = VBook(htmlBookPath)
    #  vbook.processHtmlSource() 
    # work products are in current directory
"""
    Incorporate this code -- at end should be nothing below this line
"""
