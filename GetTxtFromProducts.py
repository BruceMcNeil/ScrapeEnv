
import os,glob,shutil


class HarvestText():
    def __init__(self, baseDirectory:str = 'D:\\PRODUCTS-R1\\'):
        self.baseDirectory = baseDirectory

    def moveTextsToDirectory(self, targetDirectory:str = 'D:\\BoeksDotTxt\\') -> int:
        bookDirs = [f.path for f in os.scandir(self.baseDirectory) if f.is_dir()]
        bookCount = 0
        for b in bookDirs:
            print(b)
            itemDirs = [f.path for f in os.scandir(b) if f.is_dir()]
            for item in itemDirs:
                print(f'item: {item}')
                if ('INCOMING' in item):
                    txts = glob.iglob(os.path.join(item, '*.txt'))
                    for txt in txts:
                        if (os.path.isfile(txt)):
                            shutil.copy2(txt, targetDirectory)
                            bookCount += 1                     
        return bookCount

"""
    MAIN
"""
if __name__ == "__main__":
    h = HarvestText()
    bookC = h.moveTextsToDirectory()
    print(f'\n\n\nmoved {str(bookC)} texts.\n\n')



